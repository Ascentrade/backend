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

import os
import uvicorn
import logging
import multiprocessing

# For .env file
from dotenv import load_dotenv
load_dotenv()

from application import createApp

from utils import parseBoolean
from log_config import getNewLogger, UVICON_CONFIG


if __name__ == '__main__':
	multiprocessing.set_start_method('spawn', force=True)
	logger = getNewLogger(__name__)
	logger.info('main start')

	try:
		uvicorn.run(
			'main:createApp',
			factory=True,
			log_config=UVICON_CONFIG,
			log_level=logging._nameToLevel[os.environ.get('backend_log_level').upper()],
			access_log=parseBoolean(os.environ.get('debug')),
			host=os.environ.get('host'),
			port=int(os.environ.get('port')),
			workers=int(os.environ.get('workers'))
		)
	except Exception as e:
		logger.error('main error')
		logger.error(e)