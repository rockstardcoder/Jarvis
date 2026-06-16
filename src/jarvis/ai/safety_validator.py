from jarvis.ai.tool_manifest import ToolManifest


class SafetyValidator:

    def __init__(
        self,
        manifest: ToolManifest | None = None
    ):
        self.manifest = manifest or ToolManifest()

    def validate(
        self,
        route
    ) -> tuple[bool, dict | None, str]:
        if not isinstance(
            route,
            dict
        ):
            return False, None, "AI route is not a dictionary."

        tool_name = route.get(
            "tool"
        )

        if tool_name in [
            None,
            "",
            "none",
            "null"
        ]:
            return False, None, "AI chose no tool."

        tool_name = str(
            tool_name
        ).strip()

        tools = self.manifest.get_tools()

        if tool_name not in tools:
            return False, None, f"Tool is not allowed: {tool_name}"

        tool_data = tools[tool_name]

        if not isinstance(
            tool_data,
            dict
        ):
            return False, None, f"Invalid manifest entry for: {tool_name}"

        actions = tool_data.get(
            "actions",
            {}
        )

        if not isinstance(
            actions,
            dict
        ):
            actions = {}

        action = route.get(
            "action"
        )

        schema = None

        if action is None:
            schema = actions.get(
                "_default"
            )
        else:
            action = str(
                action
            ).strip()

            schema = actions.get(
                action
            )

        if schema is None:
            return (
                False,
                None,
                f"Action is not allowed for {tool_name}: {action}"
            )

        if not isinstance(
            schema,
            dict
        ):
            schema = {}

        required = schema.get(
            "required",
            []
        )

        optional = schema.get(
            "optional",
            []
        )

        if not isinstance(
            required,
            list
        ):
            required = []

        if not isinstance(
            optional,
            list
        ):
            optional = []

        for key in required:
            value = route.get(
                key
            )

            if value is None:
                return False, None, f"Missing required field: {key}"

            if isinstance(
                value,
                str
            ) and not value.strip():
                return False, None, f"Empty required field: {key}"

        allowed_keys = set(
            [
                "tool",
                "action"
            ]
        )

        allowed_keys.update(
            required
        )

        allowed_keys.update(
            optional
        )

        cleaned_route = {}

        for key, value in route.items():
            if key in allowed_keys:
                cleaned_route[key] = value

        cleaned_route["tool"] = tool_name

        if action is not None:
            cleaned_route["action"] = action

        return True, cleaned_route, "AI route validated."