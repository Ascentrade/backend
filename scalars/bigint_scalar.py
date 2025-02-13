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

# 12345678910111213
from ariadne import ScalarType

def serializer(value:int) -> str:
	"""Serializer for custom GrapQL scalar **BigInt**

	Args:
		value (int): Python integer value

	Raises:
		ValueError: Error if invalid BigInt

	Returns:
		str: String with BigInt representation (string of int)
	"""
	try:
		return str(value)
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid integer')


def value_parser(value:str) -> int:
	"""Value parser for custom GrapQL scalar **BigInt**

	Args:
		value (str): String with BigInt representation

	Raises:
		ValueError: Error if invalid string

	Returns:
		int: Converted BigInt object
	"""
	try:
		return int(value)
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid BigInt string')


bigintScalar = ScalarType('BigInt', serializer=serializer, value_parser=value_parser)