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

# ISO-8601
# 2025-01-06T14:41:05+0000
from ariadne import ScalarType
from datetime import datetime

def serializer(value:datetime) -> str:
	"""Serializer for custom GrapQL scalar **Datetime**

	Args:
		value (datetime): Datetime object to convert

	Raises:
		ValueError: Error if invalid datetime

	Returns:
		str: String with datetime representation
	"""
	try:
		return value.isoformat()
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid datetime string')


def value_parser(value:str) -> datetime:
	"""Value parser for custom GrapQL scalar **Datetime**

	Args:
		value (str): String with datetime representation

	Raises:
		ValueError: Error if invalid string

	Returns:
		time: Converted datetime object
	"""
	try:
		return datetime.fromisoformat(value)
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid datetime string')


datetimeScalar = ScalarType('Datetime', serializer=serializer, value_parser=value_parser)