from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import aiohttp
import os
from bs4 import BeautifulSoup
import re

app = FastAPI()

# Cache for fetched documentation
DOC_CACHE = {}

class DocumentationQuery(BaseModel):
    library: str
    term: str
    max_results: Optional[int] = 5

class CodeExampleQuery(BaseModel):
    library: str
    function: str
    language: Optional[str] = "python"
    max_examples: Optional[int] = 3

class DocumentationResult(BaseModel):
    library: str
    term: str
    results: List[Dict]
    error: Optional[str] = None

class CodeExampleResult(BaseModel):
    library: str
    function: str
    examples: List[Dict]
    error: Optional[str] = None

# Documentation sources with their base URLs
DOC_SOURCES = {
    "python": "https://docs.python.org/3/",
    "javascript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/",
    "nodejs": "https://nodejs.org/api/",
    "react": "https://reactjs.org/docs/",
    "tensorflow": "https://www.tensorflow.org/api_docs/",
    "pandas": "https://pandas.pydata.org/docs/",
    "django": "https://docs.djangoproject.com/en/stable/",
    "flask": "https://flask.palletsprojects.com/en/latest/",
    "fastapi": "https://fastapi.tiangolo.com/",
    "numpy": "https://numpy.org/doc/stable/",
    "pytorch": "https://pytorch.org/docs/stable/",
}

# Example code sources
CODE_EXAMPLE_SOURCES = {
    "python": "https://docs.python.org/3/search.html?q={}&check_keywords=yes&area=default",
    "javascript": "https://developer.mozilla.org/en-US/search?q={}",
    "nodejs": "https://nodejs.org/api/all.html#all_{}"
}

@app.post('/search_docs', response_model=DocumentationResult)
async def search_documentation(query: DocumentationQuery):
    try:
        # Check cache first
        cache_key = f"{query.library}:{query.term}"
        if cache_key in DOC_CACHE:
            return DOC_CACHE[cache_key]
        
        # Get the base URL for the requested library
        base_url = DOC_SOURCES.get(query.library.lower())
        if not base_url:
            return DocumentationResult(
                library=query.library,
                term=query.term,
                results=[],
                error=f"Documentation for {query.library} is not available"
            )
        
        # Construct search URL
        search_url = f"{base_url}search.html?q={query.term}"
        if query.library.lower() == "python":
            search_url = f"https://docs.python.org/3/search.html?q={query.term}&check_keywords=yes&area=default"
        elif query.library.lower() == "javascript":
            search_url = f"https://developer.mozilla.org/en-US/search?q={query.term}"
        
        # Fetch search results
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status != 200:
                    return DocumentationResult(
                        library=query.library,
                        term=query.term,
                        results=[],
                        error=f"Failed to fetch documentation: {response.status}"
                    )
                
                html = await response.text()
        
        # Parse search results
        soup = BeautifulSoup(html, 'lxml')
        results = []
        
        # Different parsing logic for different documentation sources
        if query.library.lower() == "python":
            search_results = soup.select('ul.search li')
            for result in search_results[:query.max_results]:
                link = result.select_one('a')
                if link:
                    href = link.get('href')
                    title = link.text.strip()
                    description = result.select_one('.context').text.strip() if result.select_one('.context') else ""
                    results.append({
                        "title": title,
                        "url": f"https://docs.python.org/3/{href}",
                        "description": description
                    })
        elif query.library.lower() == "javascript":
            search_results = soup.select('.result-list .result')
            for result in search_results[:query.max_results]:
                link = result.select_one('a')
                if link:
                    href = link.get('href')
                    title = link.text.strip()
                    description = result.select_one('.excerpt').text.strip() if result.select_one('.excerpt') else ""
                    results.append({
                        "title": title,
                        "url": f"https://developer.mozilla.org{href}",
                        "description": description
                    })
        # Add other library-specific parsing logic here
        
        # Cache the results
        result = DocumentationResult(
            library=query.library,
            term=query.term,
            results=results
        )
        DOC_CACHE[cache_key] = result
        
        return result
    except Exception as e:
        return DocumentationResult(
            library=query.library,
            term=query.term,
            results=[],
            error=str(e)
        )

@app.post('/code_examples', response_model=CodeExampleResult)
async def get_code_examples(query: CodeExampleQuery):
    try:
        # Construct search URL based on language and function
        language = query.language.lower()
        if language not in CODE_EXAMPLE_SOURCES:
            return CodeExampleResult(
                library=query.library,
                function=query.function,
                examples=[],
                error=f"Code examples for {language} are not available"
            )
        
        search_url = CODE_EXAMPLE_SOURCES[language].format(query.function)
        
        # Fetch search results
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status != 200:
                    return CodeExampleResult(
                        library=query.library,
                        function=query.function,
                        examples=[],
                        error=f"Failed to fetch code examples: {response.status}"
                    )
                
                html = await response.text()
        
        # Parse search results
        soup = BeautifulSoup(html, 'lxml')
        examples = []
        
        # Different parsing logic for different languages
        if language == "python":
            code_blocks = soup.select('pre')
            for code_block in code_blocks[:query.max_examples]:
                if query.function in code_block.text:
                    # Find the heading or description near the code block
                    heading = code_block.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    heading_text = heading.text.strip() if heading else "Example"
                    
                    examples.append({
                        "title": heading_text,
                        "code": code_block.text.strip(),
                        "language": "python"
                    })
        # Add other language-specific parsing logic here
                
        return CodeExampleResult(
            library=query.library,
            function=query.function,
            examples=examples
        )
    except Exception as e:
        return CodeExampleResult(
            library=query.library,
            function=query.function,
            examples=[],
            error=str(e)
        )

@app.get('/available_docs')
async def get_available_documentation():
    return {"available_libraries": list(DOC_SOURCES.keys())}

@app.get('/health')
async def health_check():
    return {"status": "healthy"}