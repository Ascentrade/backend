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

def securityInputFilter(input:dict={}) -> dict:
	"""Upper case filter for some keys

	Args:
		input (dict, optional): Input dict. Defaults to {}.

	Returns:
		dict: Upper case forced output dict
	"""
	for k in ['code', 'exchange_code']:
		if k in input.keys():
			input[k] = input[k].upper()
	return input


def parseBoolean(value) -> bool:
	if isinstance(value, bool):
		return value
	elif isinstance(value, str):
		if len(value) > 0 and value.lower() in ['1', 'true', 't', 'yes', 'y']:
			return True
	return False


def parseInt(value, default:int) -> int:
	"""Try to parse an integer from input (.env) or return default

	Args:
		value (Any): Any input for parsing integer
		default (int): Default if not parsable

	Returns:
		int: Parsed or default int
	"""
	try:
		if value == None:
			return default
		elif isinstance(value, int):
			return value
		elif isinstance(value, str):
			return int(value)
	except:
		pass
	return default


def dataclassFromDict(c, d):
	"""Recursive function to create a dataclass object from dictionary.

	Args:
		c (class): Dataclass reference
		d (dict): Dict to convert

	Returns:
		(class): Dataclass object
	"""
	try:
		fieldtypes = c.__annotations__
		return c(**{f: dataclassFromDict(fieldtypes[f], d[f]) for f in d})
	#except AttributeError:
	except Exception as e:
		if isinstance(d, (tuple, list)):
			return [dataclassFromDict(c.__args__[0], f) for f in d]
		return d