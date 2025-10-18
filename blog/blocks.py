from wagtail.blocks import (
    ChoiceBlock,
    StructBlock,
    TextBlock,
    RichTextBlock,
    CharBlock
)

class CodeBlock(StructBlock):
    language = ChoiceBlock(
        choices=[
            ('python', 'Python'),
            ('html', 'HTML'),
            ('css', 'CSS'),
            ('javascript', 'JavaScript'),
            ('bash', 'Bash'),
        ],
        default='python',
        required=True,
        help_text="Select the code language for syntax highlighting."
    )
    code = TextBlock(help_text="Paste your code snippet here.")

    class Meta:
        template = "blog/blocks/code_block.html"
        icon = "code"
        label = "Code Block"

class NoteBlock(StructBlock):
    title = CharBlock(required=False, help_text="Optional title for the note")
    body = RichTextBlock(features=["bold", "italic", "link", "ul", "ol"])

    class Meta:
        icon = "help"
        label = "Note"
        template = "blog/blocks/note_block.html"