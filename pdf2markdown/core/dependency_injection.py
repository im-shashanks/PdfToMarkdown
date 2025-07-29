"""
Dependency injection container for managing application dependencies.

This module provides a simple but effective dependency injection container
that supports interface registration, factory functions, and singleton management.
"""

from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Type
from typing import TypeVar

from pdf2markdown.core.config import ApplicationConfig
from pdf2markdown.domain.interfaces import CodeDetectorInterface
from pdf2markdown.domain.interfaces import DocumentAnalyzerInterface
from pdf2markdown.domain.interfaces import FormatterInterface
from pdf2markdown.domain.interfaces import HeadingDetectorInterface
from pdf2markdown.domain.interfaces import LanguageDetectorInterface
from pdf2markdown.domain.interfaces import ListDetectorInterface
from pdf2markdown.domain.interfaces import ParagraphDetectorInterface
from pdf2markdown.domain.interfaces import PdfParserStrategy

T = TypeVar('T')


class DependencyInjectionContainer:
    """
    Simple dependency injection container for managing application dependencies.
    
    Supports:
    - Interface registration with factory functions
    - Singleton management
    - Type-safe dependency resolution
    """

    def __init__(self) -> None:
        """Initialize the dependency injection container."""
        self._factories: Dict[Type, Callable[[], Any]] = {}
        self._singletons: Dict[Type, Any] = {}
        self._singleton_flags: Dict[Type, bool] = {}

    def register(
        self,
        interface: Type[T],
        factory: Callable[[], T],
        singleton: bool = False
    ) -> None:
        """
        Register a dependency with its factory function.
        
        Args:
            interface: The interface type to register
            factory: Factory function that creates the implementation
            singleton: Whether to treat as singleton (default: False)
        """
        self._factories[interface] = factory
        self._singleton_flags[interface] = singleton

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        Register a pre-created instance as a singleton.
        
        Args:
            interface: The interface type to register
            instance: The pre-created instance
        """
        self._singletons[interface] = instance
        self._singleton_flags[interface] = True

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a dependency by its interface type.
        
        Args:
            interface: The interface type to resolve
            
        Returns:
            Instance of the requested interface
            
        Raises:
            ValueError: If the interface is not registered
        """
        if interface not in self._factories and interface not in self._singletons:
            raise ValueError(f"Interface {interface.__name__} is not registered")

        # Return existing singleton if available
        if interface in self._singletons:
            return self._singletons[interface]

        # Create new instance
        factory = self._factories[interface]
        instance = factory()

        # Store as singleton if configured
        if self._singleton_flags.get(interface, False):
            self._singletons[interface] = instance

        return instance

    def is_registered(self, interface: Type) -> bool:
        """
        Check if an interface is registered.
        
        Args:
            interface: The interface type to check
            
        Returns:
            True if registered, False otherwise
        """
        return interface in self._factories or interface in self._singletons


def create_default_container(config: Optional[ApplicationConfig] = None) -> DependencyInjectionContainer:
    """
    Create a dependency injection container with default registrations.
    
    Args:
        config: Application configuration (uses default if None)
        
    Returns:
        Configured dependency injection container
    """
    from pdf2markdown.domain.services import CodeDetector
    from pdf2markdown.domain.services import HeadingDetector
    from pdf2markdown.domain.services import LanguageDetector
    from pdf2markdown.domain.services import ListDetector
    from pdf2markdown.domain.services import ParagraphDetector
    from pdf2markdown.domain.services.document_analyzer import DocumentAnalyzer
    from pdf2markdown.infrastructure.formatters import MarkdownFormatter
    from pdf2markdown.infrastructure.parsers import PdfMinerParser

    container = DependencyInjectionContainer()

    # Register configuration as singleton
    app_config = config or ApplicationConfig()
    container.register_instance(ApplicationConfig, app_config)

    # Register parser strategy
    container.register(
        PdfParserStrategy,
        lambda: PdfMinerParser(),
        singleton=False
    )

    # Register heading detector
    container.register(
        HeadingDetectorInterface,
        lambda: HeadingDetector(),
        singleton=False
    )

    # Register paragraph detector
    container.register(
        ParagraphDetectorInterface,
        lambda: ParagraphDetector(),
        singleton=False
    )

    # Register list detector
    container.register(
        ListDetectorInterface,
        lambda: ListDetector(
            indentation_threshold=app_config.list_detection.indentation_threshold,
            continuation_indent_threshold=app_config.list_detection.continuation_indent_threshold,
            max_nesting_level=app_config.list_detection.max_nesting_level
        ),
        singleton=False
    )

    # Register code detector
    container.register(
        CodeDetectorInterface,
        lambda: CodeDetector(),
        singleton=False
    )

    # Register language detector
    container.register(
        LanguageDetectorInterface,
        lambda: LanguageDetector(),
        singleton=False
    )

    # Register formatter
    container.register(
        FormatterInterface,
        lambda: MarkdownFormatter(),
        singleton=False
    )

    # Register document analyzer
    container.register(
        DocumentAnalyzerInterface,
        lambda: DocumentAnalyzer(),
        singleton=True  # Singleton since it's stateless
    )

    return container
