# GenXAI Framework - Tools System Design

**Version:** 1.0.0  
**Last Updated:** January 28, 2026  
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Tool Architecture](#tool-architecture)
3. [Built-in Tools](#built-in-tools)
4. [Tool Management](#tool-management)
5. [Custom Tools](#custom-tools)
6. [Tool Marketplace](#tool-marketplace)
7. [Implementation Examples](#implementation-examples)

---

## Overview

The GenXAI tool system provides agents with extensible capabilities to interact with external systems, process data, and perform computations. The system is designed to be:

- **Extensible**: Easy to add new tools
- **Type-Safe**: Full type checking and validation
- **Composable**: Tools can be chained together
- **Observable**: Full logging and monitoring
- **Secure**: Input validation and sandboxing

---

## Tool Architecture

### Core Components

```python
from typing import Any, Dict, List, Optional, Callable, Protocol
from pydantic import BaseModel, Field
from enum import Enum

class ToolCategory(str, Enum):
    """Tool categories for organization"""
    WEB = "web"
    DATABASE = "database"
    FILE = "file"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"
    AI = "ai"
    DATA_PROCESSING = "data_processing"
    SYSTEM = "system"
    CUSTOM = "custom"

class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern for strings
    
class ToolMetadata(BaseModel):
    """Tool metadata"""
    name: str
    description: str
    category: ToolCategory
    tags: List[str] = []
    version: str = "1.0.0"
    author: str = "GenXAI"
    license: str = "MIT"
    documentation_url: Optional[str] = None
    
class ToolResult(BaseModel):
    """Tool execution result"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    execution_time: float = 0.0

class Tool(Protocol):
    """Base protocol for all tools"""
    metadata: ToolMetadata
    parameters: List[ToolParameter]
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        ...
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters"""
        ...
    
    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAPI-style schema"""
        ...
```

### Base Tool Implementation

```python
from abc import ABC, abstractmethod
import time
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self, metadata: ToolMetadata, parameters: List[ToolParameter]):
        self.metadata = metadata
        self.parameters = parameters
        self._execution_count = 0
        self._total_execution_time = 0.0
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute tool with validation and error handling"""
        start_time = time.time()
        
        try:
            # Validate input
            if not self.validate_input(**kwargs):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Invalid input parameters"
                )
            
            # Execute tool logic
            result = await self._execute(**kwargs)
            
            # Update metrics
            execution_time = time.time() - start_time
            self._execution_count += 1
            self._total_execution_time += execution_time
            
            logger.info(f"Tool {self.metadata.name} executed successfully in {execution_time:.2f}s")
            
            return ToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    "tool": self.metadata.name,
                    "version": self.metadata.version
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool {self.metadata.name} failed: {str(e)}")
            
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=execution_time
            )
    
    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """Implement tool-specific logic"""
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters against schema"""
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False
            
            if param.name in kwargs:
                value = kwargs[param.name]
                
                # Type validation
                if param.type == "string" and not isinstance(value, str):
                    return False
                elif param.type == "number" and not isinstance(value, (int, float)):
                    return False
                elif param.type == "boolean" and not isinstance(value, bool):
                    return False
                
                # Range validation
                if param.min_value is not None and value < param.min_value:
                    return False
                if param.max_value is not None and value > param.max_value:
                    return False
                
                # Enum validation
                if param.enum and value not in param.enum:
                    return False
        
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate OpenAPI-style schema"""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "category": self.metadata.category,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                        **({"enum": param.enum} if param.enum else {}),
                        **({"default": param.default} if param.default is not None else {})
                    }
                    for param in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool execution metrics"""
        return {
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": (
                self._total_execution_time / self._execution_count 
                if self._execution_count > 0 else 0
            )
        }
```

---

## Built-in Tools

### Web Tools

#### 1. Web Search Tool
```python
class WebSearchTool(BaseTool):
    """Search the web using various providers"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="web_search",
            description="Search the internet for information",
            category=ToolCategory.WEB,
            tags=["search", "web", "internet"]
        )
        
        parameters = [
            ToolParameter(
                name="query",
                type="string",
                description="Search query"
            ),
            ToolParameter(
                name="num_results",
                type="number",
                description="Number of results to return",
                required=False,
                default=10,
                min_value=1,
                max_value=100
            ),
            ToolParameter(
                name="provider",
                type="string",
                description="Search provider",
                required=False,
                default="google",
                enum=["google", "bing", "duckduckgo"]
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, query: str, num_results: int = 10, 
                      provider: str = "google") -> List[Dict[str, str]]:
        """Execute web search"""
        # Implementation using search API
        pass
```

#### 2. Web Scraper Tool
```python
class WebScraperTool(BaseTool):
    """Extract content from web pages"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="web_scraper",
            description="Extract content from web pages",
            category=ToolCategory.WEB,
            tags=["scraping", "web", "extraction"]
        )
        
        parameters = [
            ToolParameter(name="url", type="string", description="URL to scrape"),
            ToolParameter(
                name="selector",
                type="string",
                description="CSS selector for content",
                required=False
            ),
            ToolParameter(
                name="extract_links",
                type="boolean",
                description="Extract all links",
                required=False,
                default=False
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, url: str, selector: Optional[str] = None,
                      extract_links: bool = False) -> Dict[str, Any]:
        """Scrape web page"""
        # Implementation using BeautifulSoup/Playwright
        pass
```

#### 3. API Caller Tool
```python
class APICallerTool(BaseTool):
    """Make HTTP API calls"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="api_caller",
            description="Call external APIs with authentication",
            category=ToolCategory.WEB,
            tags=["api", "http", "rest"]
        )
        
        parameters = [
            ToolParameter(name="url", type="string", description="API endpoint URL"),
            ToolParameter(
                name="method",
                type="string",
                description="HTTP method",
                enum=["GET", "POST", "PUT", "DELETE", "PATCH"]
            ),
            ToolParameter(
                name="headers",
                type="object",
                description="HTTP headers",
                required=False
            ),
            ToolParameter(
                name="body",
                type="object",
                description="Request body",
                required=False
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, url: str, method: str, 
                      headers: Optional[Dict] = None,
                      body: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API call"""
        # Implementation using httpx
        pass
```

### Database Tools

#### 4. SQL Query Tool
```python
class SQLQueryTool(BaseTool):
    """Execute SQL queries"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="sql_query",
            description="Query SQL databases",
            category=ToolCategory.DATABASE,
            tags=["sql", "database", "query"]
        )
        
        parameters = [
            ToolParameter(name="query", type="string", description="SQL query"),
            ToolParameter(
                name="connection_string",
                type="string",
                description="Database connection string"
            ),
            ToolParameter(
                name="read_only",
                type="boolean",
                description="Restrict to read-only queries",
                default=True
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, query: str, connection_string: str,
                      read_only: bool = True) -> List[Dict[str, Any]]:
        """Execute SQL query"""
        # Implementation using SQLAlchemy
        pass
```

#### 5. Vector Search Tool
```python
class VectorSearchTool(BaseTool):
    """Search vector databases"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="vector_search",
            description="Semantic search in vector databases",
            category=ToolCategory.DATABASE,
            tags=["vector", "semantic", "search"]
        )
        
        parameters = [
            ToolParameter(name="query", type="string", description="Search query"),
            ToolParameter(
                name="top_k",
                type="number",
                description="Number of results",
                default=5
            ),
            ToolParameter(
                name="index_name",
                type="string",
                description="Vector index name"
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, query: str, top_k: int = 5,
                      index_name: str = "") -> List[Dict[str, Any]]:
        """Search vector database"""
        # Implementation using Pinecone/Weaviate
        pass
```

### File Tools

#### 6. File Reader Tool
```python
class FileReaderTool(BaseTool):
    """Read files from disk"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="file_reader",
            description="Read files from disk",
            category=ToolCategory.FILE,
            tags=["file", "read", "io"]
        )
        
        parameters = [
            ToolParameter(name="path", type="string", description="File path"),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding",
                default="utf-8"
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, path: str, encoding: str = "utf-8") -> str:
        """Read file content"""
        # Implementation
        pass
```

#### 7. PDF Parser Tool
```python
class PDFParserTool(BaseTool):
    """Parse PDF documents"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="pdf_parser",
            description="Extract text and metadata from PDF files",
            category=ToolCategory.FILE,
            tags=["pdf", "parse", "document"]
        )
        
        parameters = [
            ToolParameter(name="path", type="string", description="PDF file path"),
            ToolParameter(
                name="extract_images",
                type="boolean",
                description="Extract images",
                default=False
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, path: str, extract_images: bool = False) -> Dict[str, Any]:
        """Parse PDF"""
        # Implementation using PyPDF2/pdfplumber
        pass
```

### Computation Tools

#### 8. Calculator Tool
```python
class CalculatorTool(BaseTool):
    """Perform mathematical calculations"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="calculator",
            description="Evaluate mathematical expressions",
            category=ToolCategory.COMPUTATION,
            tags=["math", "calculation", "computation"]
        )
        
        parameters = [
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression"
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, expression: str) -> float:
        """Evaluate expression"""
        # Safe evaluation using ast.literal_eval or sympy
        pass
```

#### 9. Code Executor Tool
```python
class CodeExecutorTool(BaseTool):
    """Execute code in sandboxed environment"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="code_executor",
            description="Execute code safely in sandbox",
            category=ToolCategory.COMPUTATION,
            tags=["code", "execution", "sandbox"]
        )
        
        parameters = [
            ToolParameter(name="code", type="string", description="Code to execute"),
            ToolParameter(
                name="language",
                type="string",
                description="Programming language",
                enum=["python", "javascript", "bash"]
            ),
            ToolParameter(
                name="timeout",
                type="number",
                description="Execution timeout in seconds",
                default=30
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, code: str, language: str, 
                      timeout: int = 30) -> Dict[str, Any]:
        """Execute code"""
        # Implementation using Docker/subprocess with timeout
        pass
```

### Communication Tools

#### 10. Email Sender Tool
```python
class EmailSenderTool(BaseTool):
    """Send emails"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="email_sender",
            description="Send emails via SMTP",
            category=ToolCategory.COMMUNICATION,
            tags=["email", "smtp", "communication"]
        )
        
        parameters = [
            ToolParameter(name="to", type="string", description="Recipient email"),
            ToolParameter(name="subject", type="string", description="Email subject"),
            ToolParameter(name="body", type="string", description="Email body"),
            ToolParameter(
                name="html",
                type="boolean",
                description="Send as HTML",
                default=False
            )
        ]
        
        super().__init__(metadata, parameters)
    
    async def _execute(self, to: str, subject: str, body: str,
                      html: bool = False) -> Dict[str, Any]:
        """Send email"""
        # Implementation using aiosmtplib
        pass
```

---

## Tool Management

### Tool Registry

```python
class ToolRegistry:
    """Central registry for all tools"""
    
    _instance = None
    _tools: Dict[str, BaseTool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Register a new tool"""
        if tool.metadata.name in cls._tools:
            logger.warning(f"Tool {tool.metadata.name} already registered, overwriting")
        cls._tools[tool.metadata.name] = tool
        logger.info(f"Registered tool: {tool.metadata.name}")
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a tool"""
        if name in cls._tools:
            del cls._tools[name]
            logger.info(f"Unregistered tool: {name}")
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return cls._tools.get(name)
    
    @classmethod
    def list_all(cls) -> List[BaseTool]:
        """List all registered tools"""
        return list(cls._tools.values())
    
    @classmethod
    def search(cls, query: str, category: Optional[ToolCategory] = None) -> List[BaseTool]:
        """Search tools by query and category"""
        results = []
        query_lower = query.lower()
        
        for tool in cls._tools.values():
            # Filter by category
            if category and tool.metadata.category != category:
                continue
            
            # Search in name, description, and tags
            if (query_lower in tool.metadata.name.lower() or
                query_lower in tool.metadata.description.lower() or
                any(query_lower in tag.lower() for tag in tool.metadata.tags)):
                results.append(tool)
        
        return results
    
    @classmethod
    def list_categories(cls) -> List[ToolCategory]:
        """List all tool categories"""
        return list(set(tool.metadata.category for tool in cls._tools.values()))
    
    @classmethod
    def get_by_category(cls, category: ToolCategory) -> List[BaseTool]:
        """Get all tools in a category"""
        return [tool for tool in cls._tools.values() 
                if tool.metadata.category == category]
```

### Tool Orchestrator

```python
class ToolOrchestrator:
    """Intelligent tool selection and execution"""
    
    def __init__(self, agent: 'Agent'):
        self.agent = agent
        self.registry = ToolRegistry()
    
    async def select_tools(self, task: str) -> List[BaseTool]:
        """Use LLM to select appropriate tools for task"""
        available_tools = self.registry.list_all()
        tool_descriptions = [
            f"{tool.metadata.name}: {tool.metadata.description}"
            for tool in available_tools
        ]
        
        prompt = f"""
        Task: {task}
        
        Available tools:
        {chr(10).join(tool_descriptions)}
        
        Select the most appropriate tools for this task.
        Return a JSON array of tool names.
        """
        
        response = await self.agent.llm.generate(prompt)
        selected_names = json.loads(response)
        
        return [self.registry.get(name) for name in selected_names 
                if self.registry.get(name)]
    
    async def execute_with_retry(self, tool: BaseTool, max_retries: int = 3,
                                **kwargs) -> ToolResult:
        """Execute tool with retry logic"""
        for attempt in range(max_retries):
            result = await tool.execute(**kwargs)
            
            if result.success:
                return result
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"Tool {tool.metadata.name} failed (attempt {attempt + 1}), "
                    f"retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
        
        return result
```

---

## Custom Tools

### Creating Custom Tools

#### From Python Function
```python
class ToolFactory:
    """Create tools dynamically"""
    
    @staticmethod
    def from_function(func: Callable, metadata: ToolMetadata,
                     parameters: List[ToolParameter]) -> BaseTool:
        """Create tool from Python function"""
        
        class CustomTool(BaseTool):
            def __init__(self):
                super().__init__(metadata, parameters)
                self.func = func
            
            async def _execute(self, **kwargs) -> Any:
                if asyncio.iscoroutinefunction(self.func):
                    return await self.func(**kwargs)
                return self.func(**kwargs)
        
        return CustomTool()

# Usage
def my_custom_function(text: str, count: int) -> str:
    return text * count

tool = ToolFactory.from_function(
    func=my_custom_function,
    metadata=ToolMetadata(
        name="text_repeater",
        description="Repeat text multiple times",
        category=ToolCategory.CUSTOM
    ),
    parameters=[
        ToolParameter(name="text", type="string", description="Text to repeat"),
        ToolParameter(name="count", type="number", description="Number of repetitions")
    ]
)

ToolRegistry.register(tool)
```

#### From OpenAPI Specification
```python
@staticmethod
def from_openapi(spec: Dict[str, Any]) -> BaseTool:
    """Create tool from OpenAPI specification"""
    # Parse OpenAPI spec
    # Generate tool metadata and parameters
    # Create tool that makes HTTP calls
    pass
```

---

## Tool Marketplace

### YAML Configuration
```yaml
# Custom tool configuration
tools:
  - name: "custom_crm_tool"
    type: "api"
    category: "custom"
    description: "Interact with CRM system"
    config:
      base_url: "https://api.mycrm.com"
      auth:
        type: "bearer"
        token: "${CRM_API_KEY}"
      endpoints:
        - name: "get_customer"
          method: "GET"
          path: "/customers/{id}"
          parameters:
            - name: "id"
              type: "string"
              required: true
        - name: "create_ticket"
          method: "POST"
          path: "/tickets"
          parameters:
            - name: "title"
              type: "string"
            - name: "description"
              type: "string"
```

---

## Implementation Examples

### Complete Tool List (50+ Tools)

**Web Tools (10)**
1. web_search
2. web_scraper
3. api_caller
4. url_validator
5. sitemap_parser
6. rss_reader
7. http_monitor
8. dns_lookup
9. whois_lookup
10. ssl_checker

**Database Tools (8)**
11. sql_query
12. vector_search
13. graph_query
14. redis_cache
15. mongodb_query
16. elasticsearch_search
17. database_backup
18. schema_inspector

**File Tools (10)**
19. file_reader
20. file_writer
21. pdf_parser
22. csv_parser
23. json_parser
24. xml_parser
25. image_analyzer
26. video_processor
27. audio_transcriber
28. file_compressor

**Computation Tools (8)**
29. calculator
30. code_executor
31. data_analyzer
32. statistical_analyzer
33. ml_predictor
34. regex_matcher
35. hash_generator
36. encryption_tool

**Communication Tools (8)**
37. email_sender
38. slack_notifier
39. sms_sender
40. webhook_caller
41. discord_notifier
42. teams_notifier
43. telegram_bot
44. twitter_poster

**AI Tools (6)**
45. text_summarizer
46. sentiment_analyzer
47. entity_extractor
48. language_detector
49. translation_tool
50. image_generator

---

**Document Status**: Living document, updated as tools are implemented.
