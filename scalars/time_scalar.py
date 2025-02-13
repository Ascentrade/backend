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

# 01:12:45
from ariadne import ScalarType
from datetime import time

def serializer(value:time) -> str:
	"""Serializer for custom GrapQL scalar **Time**

	Args:
		value (time): Time object to convert

	Raises:
		ValueError: Error if invalid time

	Returns:
		str: String with time representation
	"""
	try:
		return value.isoformat()
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid time string')


def value_parser(value:str) -> time:
	"""Value parser for custom GrapQL scalar **Time**

	Args:
		value (str): String with time representation

	Raises:
		ValueError: Error if invalid string

	Returns:
		time: Converted time object
	"""
	try:
		return time.fromisoformat(value)
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid time string')


timeScalar = ScalarType('Time', serializer=serializer, value_parser=value_parser)