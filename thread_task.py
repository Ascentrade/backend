async def resolve_startCalculations(_, info:GraphQLResolveInfo):
    # Start calculation with many IDs
	thread = threading.Thread(target=startIndicatorCalculation, args=(ids,))
	thread.daemon = False
	thread.start()


# Sync wrapper function for multiprocessing pool
def startIndicatorCalculation(ids:list) -> list:
	#print(f'startIndicatorCalculation with {len(ids)} IDs')
	try:
		with Pool(processes=os.cpu_count() - 1) as pool:
			results = pool.map(calculateMultiprocessing, ids)
			return results
	except Exception as e:
		print(e)


