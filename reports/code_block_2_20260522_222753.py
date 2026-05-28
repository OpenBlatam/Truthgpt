import arxiv

def fetch_relevant_papers(query, max_results=3):
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    papers = []
    for paper in client.results(search):
        papers.append({"id": paper.entry_id, "title": paper.title, "summary": paper.summary[:200]})
    return papers