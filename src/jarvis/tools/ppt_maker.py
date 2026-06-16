from jarvis.tools.base_tool import BaseTool
from jarvis.services.ppt_maker import PPTMaker


class PPTMakerTool(BaseTool):

    name = "ppt_maker"

    def execute(
        self,
        action: str,
        topic: str | None = None,
        style: str = "professional"
    ):

        ppt_maker = PPTMaker()

        if action == "create_ppt":
            if not topic:
                return "No presentation topic was provided."

            return ppt_maker.create_presentation(
                topic=topic,
                style=style
            )

        if action == "open_ppt_folder":
            return ppt_maker.open_presentation_folder()

        return f"Unknown PPT action: {action}"