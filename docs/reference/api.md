# API Reference

Full API reference, generated from docstrings.

## Public API

### Decorator

::: django_autowired.registry.injectable

### Scope

::: django_autowired.scopes.Scope

### Container

::: django_autowired.container.initialize
::: django_autowired.container.get
::: django_autowired.container.override
::: django_autowired.container.reset
::: django_autowired.container.is_initialized
::: django_autowired.container.get_backend_instance

## Exceptions

::: django_autowired.exceptions.AutowiredError
::: django_autowired.exceptions.ContainerNotInitializedError
::: django_autowired.exceptions.ContainerAlreadyInitializedError
::: django_autowired.exceptions.DuplicateBindingError
::: django_autowired.exceptions.BackendNotInstalledError
::: django_autowired.exceptions.UnresolvableTypeError

## Registry

::: django_autowired.registry.Registration

## Backends

::: django_autowired.backends.base.AbstractBackend
::: django_autowired.backends.injector_.InjectorBackend
::: django_autowired.backends.lagom_.LagomBackend
::: django_autowired.backends.wireup_.WireupBackend
::: django_autowired.backends.dishka_.DishkaBackend

## Integrations

::: django_autowired.integrations.django.apps.AutowiredAppConfig
::: django_autowired.integrations.fastapi.lifespan.autowired_lifespan
::: django_autowired.integrations.fastapi.lifespan.Provide
::: django_autowired.integrations.flask.extension.Autowired
::: django_autowired.integrations.flask.extension.inject_dep

## Testing utilities

::: django_autowired.testing.autowired_container
::: django_autowired.testing.build_container
::: django_autowired.testing.container_context
::: django_autowired.testing.ContainerFactory
::: django_autowired.testing.InMemoryOverrideModule
