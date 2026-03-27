from db.session import Base
from sqlalchemy import JSON, Column, Integer, BigInteger, Date, DateTime, Numeric, Text, func


class UserModel(Base):
	__tablename__ = "users"
	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	created_at = Column(DateTime, nullable=False, server_default=func.now())
	updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
	email = Column(Text, nullable=True)
	# Stripe subscription fields
	stripe_customer_id = Column(Text, nullable=True, unique=True)
	stripe_subscription_id = Column(Text, nullable=True, unique=True)
	subscription_status = Column(Text, nullable=True) # active, trialing, past_due, canceled, unpaid
	subscription_plan = Column(Text, nullable=True) # monthly, yearly
	trial_end_date = Column(DateTime, nullable=True)


class HistoricalDataModel(Base):
	__tablename__ = "historical_data"

	id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
	created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
	updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now())
	date = Column(Date, nullable=False, index=True)
	open = Column(Numeric, nullable=False)
	high = Column(Numeric, nullable=False)
	low = Column(Numeric, nullable=False)
	close = Column(Numeric, nullable=False)
	volume = Column(Numeric)
	# Indicators
	## Moving averages
	ema_20 = Column(Numeric(20, 4), nullable=True)
	sma_50 = Column(Numeric(20, 4), nullable=True)
	sma_200 = Column(Numeric(20, 4), nullable=True)
	## RSI
	rsi = Column(Numeric(20, 4), nullable=True)
	## Bollinger Bands
	bb_pc = Column(Numeric(20, 4), nullable=True)
	## ADX/DMI
	adx = Column(Numeric(20, 4), nullable=True)
	dmip = Column(Numeric(20, 4), nullable=True)
	dmim = Column(Numeric(20, 4), nullable=True)
	

class AiResponseModel(Base):
	__tablename__ = "ai_responses"

	id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
	created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
	updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now())
	timestamp = Column(DateTime(timezone=False), nullable=False, index=True)
	prompt = Column(Text, nullable=False)
	data = Column(JSON, nullable=False)
	response = Column(Text, nullable=False)
	confidence = Column(Integer, nullable=False)
	score = Column(Integer, nullable=False)
