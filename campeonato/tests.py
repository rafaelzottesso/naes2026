from django.core.paginator import Paginator
from django.test import RequestFactory, SimpleTestCase

from .templatetags.pagination_tags import pagination_page_range, pagination_query


class PaginationTagTests(SimpleTestCase):
	def test_pagination_query_preserves_repeated_filters(self):
		request = RequestFactory().get(
			'/lista/?nome=arena&nome=campus&page=4&status=1'
		)

		query = pagination_query({'request': request}, page=2)

		self.assertEqual(
			query,
			'?nome=arena&nome=campus&page=2&status=1',
		)

	def test_page_range_elides_distant_pages(self):
		paginator = Paginator(range(1000), 10)
		page_obj = paginator.page(50)

		page_range = pagination_page_range({
			'paginator': paginator,
			'page_obj': page_obj,
		})

		self.assertEqual(
			list(page_range),
			[1, paginator.ELLIPSIS, 49, 50, 51, paginator.ELLIPSIS, 100],
		)
