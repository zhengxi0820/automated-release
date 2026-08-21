from .aihot import AIHOTSource
from .github_trending import GitHubTrendingSource
from .placeholder import NotImplementedSource

SOURCE_REGISTRY = {
    "aihot": AIHOTSource,
    "github_trending": GitHubTrendingSource,
    "weibo_hot": lambda domain_id, params: NotImplementedSource("weibo_hot", domain_id, params),
    "zhihu_hot": lambda domain_id, params: NotImplementedSource("zhihu_hot", domain_id, params),
    "toutiao_hot": lambda domain_id, params: NotImplementedSource("toutiao_hot", domain_id, params),
    "baidu_hot": lambda domain_id, params: NotImplementedSource("baidu_hot", domain_id, params),
}


def get_source(name: str, domain_id: str, params: dict):
    cls = SOURCE_REGISTRY.get(name)
    if cls is None:
        raise KeyError(f"未知数据源: {name}")
    return cls(domain_id, params)
