"""
 @copyright Copyright (C) 2024 Dennis Greguhn <dev@greguhn.de>
 
 @author Dennis Greguhn <dev@greguhn.de>
 
 @license AGPL-3.0-or-later
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.
 
 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import multiprocessing
import os
import json
from uuid import uuid4
import asyncio
from multiprocessing import Pool
from datetime import datetime, timezone
from dataclasses import dataclass, is_dataclass, asdict

import asyncpg

from utils import parseInt
from log_config import getNewLogger
from database import DatabaseConnector
from indicator_factory import IndicatorFactory


@dataclass
class BackgroundJobData:
	"""Class to handle open tasks to queue"""
	timestamp: int
	uuid: str
	table: str
	id1: int
	id2: int
	date1: str
	date2: str
	data: dict

	def __init__(
		self,
		table: str,
		id1: int = None,
		id2: int = None,
		date1: str = None,
		date2: str = None,
		data: dict = {},
		timestamp: int = None,
		uuid: str = None
	):
		self.table = table
		self.id1 = id1
		self.id2 = id2
		self.date1 = date1
		self.date2 = date2
		self.data = data
		# Addidional for logging and filtering
		self.timestamp = timestamp if timestamp != None else int(datetime.utcnow().timestamp())
		self.uuid = uuid if uuid != None else str(uuid4())
	

	@classmethod
	def fromDict(cls, dictIn:dict) -> BackgroundJobData:
		return BackgroundJobData(
			table = dictIn['table'],
			id1 = dictIn['id1'],
			id2 = dictIn['id2'],
			date1 = dictIn['date1'],
			date2 = dictIn['date2'],
			data = dictIn['data'],
			timestamp = dictIn['timestamp'],
			uuid = dictIn['uuid']
		)


@dataclass
class BackgroundJobResult:
	"""Class to return background processing task results"""
	timestamp: int
	data: BackgroundJobData
	success: bool
	exception: Exception

	def __init__(
		self,
		data: BackgroundJobData,
		success: bool,
		exception: Exception = None
	):
		self.timestamp = int(datetime.now(tz=timezone.utc).timestamp())
		self.data = data
		self.success = success
		self.exception = exception


class EnhancedJSONEncoder(json.JSONEncoder):
	"""Custom JSON encoder to also encode dataclasses"""
	def default(self, o):
		if is_dataclass(o):
			return asdict(o)
		return super().default(o)


class TaskHandler:
	"""Class to handle background jobs like calculating indicators"""
	dbCon:DatabaseConnector = None
	factory:IndicatorFactory = None
	parallelProcesses:int = None
	
	def __init__(self, dbCon:DatabaseConnector):
		"""Init method

		Args:
			dbCon (DatabaseConnector): Database class instance.
		"""
		self.logger = getNewLogger('task-handler')
		self.logger.info(f'TaskHandler.__init__')
		self.dbCon = dbCon
		try:
			self.parallelProcesses = int(multiprocessing.cpu_count()/2.0)
		except:
			self.parallelProcesses = 1
			self.logger.warning(f'Unable to read CPU count, fallback to 1 process')

		self.parallelProcesses = parseInt(os.environ.get('parallelProcesses'), self.parallelProcesses)
		self.logger.info(f'Using {self.parallelProcesses} process to calculate indicators')
		self.jobQueue = asyncio.Queue()
		self.backgroundTasks = set()
		self.shutdownRequest = False
		self.factory = IndicatorFactory(dbCon)

		self.indicatorConfig = {}
		with open('indicators.json', 'r') as f:
			self.indicatorConfig = json.loads(f.read())

		# Init task scheduling timer
		self.task = asyncio.ensure_future(self.scheduleTasks())


	async def loadJobs(self) -> bool:
		"""Async function to load all jobs from backup file

		Returns:
			bool: True if >0 jobs loaded, otherwise False
		"""
		returnValue = False
		try:
			with open('jobs.json', 'r') as f:
				backup = json.loads(f.read())
				if backup != None and type(backup) == list:
					if len(backup) > 0:
						for job in backup:
							self.logger.debug(f'Load backup job {job}')
							await self.jobQueue.put(BackgroundJobData.fromDict(job))
						self.logger.info(f'Loaded {self.jobQueue.qsize()} backuped jobs from file')
						returnValue = True
					else:
						self.logger.info(f'No jobs in backup file')
				else:
					self.logger.warning('Backup file "jobs.json" contains no valid job backup')
		except Exception as e:
			self.logger.warning(f'Unable to load file "jobs.json"')
			self.logger.warning(e)
		return returnValue


	async def addJob(self, jobData:BackgroundJobData):
		"""Add a background job to the queue.

		Args:
			jobData (BackgroundJobData): Information about what to update.
		"""
		self.logger.debug(f'Add job "{jobData.table}" with data={jobData.data} and ID {jobData.uuid}')
		await self.jobQueue.put(jobData)
		self.logger.debug(f'{self.jobQueue.qsize()} jobs in queue')


	async def shutdown(self):
		"""Function to be called before shutdown the application.
		
			Stop all running tasks and save them into the backup file.
		"""
		# Set shutdownRequest and wait for tasks to finish
		try:
			self.logger.info('TaskHandler.shutdown()')
			self.shutdownRequest = True
			self.task.cancel()
			# Wait until all running tasks are finished
			while len(self.backgroundTasks) > 0:
				self.logger.info(f'Wait for {len(self.backgroundTasks)} tasks to finish...')
				await asyncio.sleep(1)
		except Exception as e:
			self.logger.error(e)
		
		# Backup all jobs
		try:
			# dequeue oll objects...
			jobs = []
			while self.jobQueue.qsize() > 0:
				jobs.append(await self.jobQueue.get())
			# ...and dump to file
			self.logger.info(f'Write {len(jobs)} jobs to "jobs.json" backup file')
			with open('jobs.json', 'w') as f:
				f.write(json.dumps(jobs, cls=EnhancedJSONEncoder))
		except Exception as e:
			self.logger.error(e)
	

	async def processingTask(self, jobData:BackgroundJobData) -> BackgroundJobResult:
		"""Processing task function.

		Args:
			jobData (BackgroundJobData): Job data from the queue.

		Returns:
			BackgroundJobResult: Result object with information about the execution.
		"""
		self.logger.debug(f'processingTask({jobData})')
		try:
			# Different jobs after updates
			if jobData.table == 'quotes':
				# TODO: Save process to check!
				p = multiprocessing.Process(target=self.factory.calculateMultiprocessing, args=(jobData.id1, self.indicatorConfig))
				p.start()
			elif jobData.table == 'securities':
				pass
			else:
				self.logger.warning(f'No background processing job for table "{jobData.table}" defined')
			return BackgroundJobResult(jobData, True)
		except Exception as e:
			self.logger.error(f'Error at processing task for {jobData}')
			self.logger.error(e)
			return BackgroundJobResult(jobData, False, e)


	def taskFinishedCallback(self, task:asyncio.Task):
		"""Callback function for every finished **processingTask**.

		Args:
			task (asyncio.Task): The finished task object.
		"""
		try:
			result:BackgroundJobResult = task.result()
			job = f'"{result.data.table}" with data={result.data} and ID {result.data.uuid}'
			if result.success == True:
				self.logger.info(f'Job successfully finished | {job}')
			else:
				self.logger.warning(f'Job error | {job}, error={result.exception}')
		except Exception as e:
			self.logger.warning(f'Error while processing job callback | {job}, error={result.exception}')
			self.logger.warning(e)


	async def scheduleTasks(self):
		"""Always running task function to check queued jobs and start them."""
		workingOnTasks = False
		try:
			# Endless loop to create new tasks unless shutdown is not requested
			while self.shutdownRequest == False:
				while len(multiprocessing.active_children()) < self.parallelProcesses and self.jobQueue.qsize() > 0:
					jobData:BackgroundJobData = await self.jobQueue.get()
					# Different jobs after updates
					if jobData.table == 'quotes':
						p = multiprocessing.Process(target=self.factory.calculateMultiprocessing, args=(jobData.id1, self.indicatorConfig))
						p.start()
					else:
						self.logger.warning(f'No background processing job for table "{jobData.table}" defined')

				if self.jobQueue.qsize() > 0:
					workingOnTasks = True
					self.logger.info(f'Active processes={len(multiprocessing.active_children())}, queue={self.jobQueue.qsize()}')
				else:
					if workingOnTasks == True:
						self.logger.info(f'All processes finished!')
					workingOnTasks = False

				await asyncio.sleep(5)
		except Exception as e:
			self.logger.error(f'Error at TaskHandler.scheduleTasks')
			self.logger.error(e)
		self.logger.info(f'TaskHandler.scheduleTasks ended')