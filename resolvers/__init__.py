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

from .country import Country
from .currency import Currency
from .exchange import Exchange
from .exchange_holiday import ExchangeHoliday
from .gics_code import GICSCode
from .mutation import Mutation
from .query import Query
from .security import Security
from .security_quote import SecurityQuote
from .split import Split
from .dividend import Dividend
from .analyst_rating import AnalystRating
from .etf_data import ETFData
from .outstanding_shares import OutstandingShares

custom_resolvers = [
	Country,
	Currency,
	Exchange,
	ExchangeHoliday,
	GICSCode,
	Mutation,
	Query,
	Security,
	SecurityQuote,
	Split,
	Dividend,
	AnalystRating,
	ETFData,
	OutstandingShares,
]