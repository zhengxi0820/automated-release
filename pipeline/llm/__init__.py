from .deepseek import DeepSeekProvider

PROVIDER_REGISTRY = {"deepseek": DeepSeekProvider}


def get_provider(name: str):
    cls = PROVIDER_REGISTRY.get(name)
    if cls is None:
        raise KeyError(f"未知模型提供商: {name}")
    return cls()
