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

# 2023-08-02
from ariadne import ScalarType
from datetime import date


def serializer(value:date) -> str:
	"""Serializer for custom GrapQL scalar **Date**

	Args:
		value (date): datetime.date object

	Raises:
		ValueError: If no valid date

	Returns:
		str: String with parsed date in ISO format like 2024-01-12
	"""
	try:
		return value.isoformat()
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid date')


def value_parser(value:str) -> date:
	"""Value parser for custom GrapQL scalar **Date**

	Args:
		value (str): String of ISO formatted date

	Raises:
		ValueError: If no valid string in ISO format

	Returns:
		date: Parsed datetime.date object
	"""
	try:
		return  date.fromisoformat(value)
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid ISO date string')


dateScalar = ScalarType('Date', serializer=serializer, value_parser=value_parser)