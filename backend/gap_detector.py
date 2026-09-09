def check_coverage(question, retrieved_results):
    """
    Inspects retrieved chunks and their metadata from ChromaDB.
    Returns {'has_gap': True, 'message': ...} if no good matches are found.
    Otherwise returns {'has_gap': False}.
    """
    if not retrieved_results:
        return {'has_gap': True, 'message': 'No documents were retrieved to answer this question.'}

    # Threshold for ChromaDB distance.
    # L2 distance above 1.5 generally indicates poor semantic similarity for default sentence-transformers.
    DISTANCE_THRESHOLD = 1.5 
    
    all_poor_matches = True
    available_sources = set()

    for chunk in retrieved_results:
        source = chunk.get('metadata', {}).get('source', 'Unknown Document')
        available_sources.add(source)
        
        distance = chunk.get('distance')
        if distance is None or distance <= DISTANCE_THRESHOLD:
            all_poor_matches = False

    if all_poor_matches:
        sources_list = ", ".join(sorted(list(available_sources)))
        if not sources_list:
            sources_list = "None"
            
        message = (f"No documents in the current dataset appear to cover this topic. "
                   f"The available reports span [{sources_list}], and none directly address this question.")
        return {'has_gap': True, 'message': message}
        
    return {'has_gap': False}
