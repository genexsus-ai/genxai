"""State schema definition and validation."""

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field, create_model, ConfigDict


class StateSchema(BaseModel):
    """Schema for workflow state."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    fields: Dict[str, Type[Any]] = Field(default_factory=dict)
    required_fields: set[str] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)


    def validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate state against schema.

        Args:
            state: State dictionary to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        missing_fields = self.required_fields - set(state.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Type validation
        for field_name, field_type in self.fields.items():
            if field_name in state:
                value = state[field_name]
                if not isinstance(value, field_type):
                    raise ValueError(
                        f"Field '{field_name}' has wrong type. "
                        f"Expected {field_type}, got {type(value)}"
                    )

        return True

    def create_pydantic_model(self, model_name: str = "DynamicState") -> Type[BaseModel]:
        """Create a Pydantic model from the schema.

        Args:
            model_name: Name for the generated model

        Returns:
            Pydantic model class
        """
        field_definitions = {}
        for field_name, field_type in self.fields.items():
            if field_name in self.required_fields:
                field_definitions[field_name] = (field_type, ...)
            else:
                field_definitions[field_name] = (Optional[field_type], None)

        return create_model(model_name, **field_definitions)

    def add_field(
        self, name: str, field_type: Type[Any], required: bool = False
    ) -> None:
        """Add a field to the schema.

        Args:
            name: Field name
            field_type: Field type
            required: Whether field is required
        """
        self.fields[name] = field_type
        if required:
            self.required_fields.add(name)

    def remove_field(self, name: str) -> None:
        """Remove a field from the schema.

        Args:
            name: Field name to remove
        """
        if name in self.fields:
            del self.fields[name]
        if name in self.required_fields:
            self.required_fields.remove(name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "fields": {name: str(type_) for name, type_ in self.fields.items()},
            "required_fields": list(self.required_fields),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSchema":
        """Create schema from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            StateSchema instance
        """
        schema = cls()
        schema.required_fields = set(data.get("required_fields", []))
        schema.metadata = data.get("metadata", {})
        # Note: Type reconstruction from string would need eval or mapping
        return schema
