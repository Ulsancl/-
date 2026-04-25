import pytest
from jinja2.exceptions import SecurityError

from autogpt_server.blocks.text import FillTextTemplateBlock


def test_fill_text_template_block_formats_templates():
    block = FillTextTemplateBlock()

    outputs = list(
        block.execute(
            {
                "values": {"name": "Alice", "greeting": "Hello"},
                "format": "{greeting}, {{name}}!",
            }
        )
    )

    assert outputs == [("output", "Hello, Alice!")]


def test_fill_text_template_block_blocks_ssti_payloads():
    block = FillTextTemplateBlock()

    with pytest.raises(SecurityError):
        list(
            block.execute(
                {
                    "values": {},
                    "format": "{{ cycler.__init__.__globals__.os.popen('id').read() }}",
                }
            )
        )
