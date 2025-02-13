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

from ariadne import ScalarType
import json
from decimal import Decimal
from datetime import date, time


class CustomEncoder(json.JSONEncoder):
	"""Custom JSON encoder to convert Decimal and time/date types
	"""
	def default(self, obj):
		if isinstance(obj, Decimal):
			return str(obj)
		elif isinstance(obj, date) or isinstance(obj, time):
			return obj.isoformat()
		# Base class
		return super().default(obj)


def serializer(value:dict) -> dict:
	"""Serializer for custom GrapQL scalar **JSON**

	Args:
		value (dict): Dictionary object to convert

	Raises:
		ValueError: Error if invalid JSON

	Returns:
		dict: Dict/JSON with converted decimal and time/date
	"""
	try:
		return json.loads(json.dumps(value, cls=CustomEncoder))
	except (ValueError, TypeError):
		raise ValueError(f'"{value}" is not a valid JSON string')


def value_parser(value:dict) -> dict:
	return value


jsonScalar = ScalarType('JSON', serializer=serializer, value_parser=value_parser)