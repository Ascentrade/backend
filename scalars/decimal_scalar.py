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

# 3.14159
from ariadne import ScalarType
from decimal import Decimal


def serializer(value:Decimal) -> str:
	"""Serializer for custom GrapQL scalar **Decimal**

	Args:
		value (Decimal): Decimal value

	Raises:
		ValueError: If string conversion fails

	Returns:
		str: Decimal number string
	"""
	try:
		return str(value)
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid decimal')


def value_parser(value:str) -> Decimal:
	"""Value parser for custom GrapQL scalar **Decimal**

	Args:
		value (str): String representation of decimal number

	Raises:
		ValueError: If conversion to Decimal fails

	Returns:
		Decimal: Decimal type
	"""
	try:
		return Decimal(value)
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid decimal')


decimalScalar = ScalarType('Decimal', serializer=serializer, value_parser=value_parser)