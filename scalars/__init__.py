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

from .bigint_scalar import bigintScalar
from .date_scalar import dateScalar
from .decimal_scalar import decimalScalar
from .json_scalar import jsonScalar
from .time_scalar import timeScalar
from .datetime_scalar import datetimeScalar

# https://ariadne.readthedocs.io/en/0.3.0/scalars.html

custom_scalars = [
	bigintScalar,
	dateScalar,
	decimalScalar,
	jsonScalar,
	timeScalar,
	datetimeScalar,
]