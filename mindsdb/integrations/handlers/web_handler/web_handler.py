import pandas as pd
from mindsdb.integrations.libs.response import HandlerStatusResponse
from mindsdb_sql.parser import ast
from mindsdb.integrations.libs.api_handler import APIHandler, APITable
from mindsdb.utilities.config import Config
from mindsdb.integrations.utilities.sql_utils import extract_comparison_conditions, project_dataframe
from mindsdb.utilities.security import validate_urls
from .urlcrawl_helpers import get_all_websites


class CrawlerTable(APITable):

    def __init__(self, handler: APIHandler):
        super().__init__(handler)
        self.config = Config()

    def select(self, query: ast.Select) -> pd.DataFrame:
        """
        Selects data from the provided websites

        Args:
            query (ast.Select): Given SQL SELECT query

        Returns:
            dataframe: Dataframe containing the crawled data

        Raises:
            NotImplementedError: If the query is not supported
        """
        conditions = extract_comparison_conditions(query.where)
        urls = []
        for operator, arg1, arg2 in conditions:
            if operator == 'or':
                raise NotImplementedError('OR is not supported')
            if arg1 == 'url':
                if operator in ['=', 'in']:
                    urls = [str(arg2)] if isinstance(arg2, str) else arg2
                else:
                    raise NotImplementedError('Invalid URL format. Please provide a single URL like url = "example.com" or'
                                              'multiple URLs using the format url IN ("url1", "url2", ...)')

        if len(urls) == 0:
            raise NotImplementedError(
                'You must specify what url you want to crawl, for example: SELECT * FROM crawl WHERE url = "someurl"')

        # Primary check: iterate through URLs and check if any are private or invalid.
        for single_url in urls:
            if is_private_url(single_url):
                raise ValueError(f"The URL '{single_url}' is private, its hostname cannot be resolved, or it is otherwise invalid. Web crawling from such URLs is not permitted.")

        # Secondary check: validate against allowed sites if configured.
        allowed_urls = self.config.get('web_crawling_allowed_sites', [])
        if allowed_urls and not validate_urls(urls, allowed_urls): # `urls` is a list
            raise ValueError(f"One or more provided URLs are not allowed for web crawling. Allowed sites are: {', '.join(allowed_urls)}.")
        
        if query.limit is None:
            raise NotImplementedError('You must specify a LIMIT clause which defines the number of pages to crawl')

        limit = query.limit.value

        result = get_all_websites(urls, limit, html=False)
        if len(result) > limit:
            result = result[:limit]
        # filter targets
        result = project_dataframe(result, query.targets, self.get_columns())
        return result

    def get_columns(self):
        """
        Returns the columns of the crawler table
        """
        return [
            'url',
            'text_content',
            'error'
        ]


class WebHandler(APIHandler):
    """
    Web handler, handling crawling content from websites.
    """
    def __init__(self, name=None, **kwargs):
        super().__init__(name)
        crawler = CrawlerTable(self)
        self._register_table('crawler', crawler)

    def check_connection(self) -> HandlerStatusResponse:
        """
        Checks the connection to the web handler
        @TODO: Implement a better check for the connection

        Returns:
            HandlerStatusResponse: Response containing the status of the connection. Hardcoded to True for now.
        """
        response = HandlerStatusResponse(True)
        return response
