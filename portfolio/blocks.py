from base.blocks import BaseStreamBlock

# import ImageBlock:
from wagtail.images.blocks import ImageBlock



# import CharBlock, ListBlock, PageChooserBlock, PageChooserBlock, RichTextBlock, and StructBlock:
from wagtail.blocks import (
    CharBlock,
    ListBlock,
    PageChooserBlock,
    RichTextBlock,
    StructBlock,
)



# add CardBlock:
class CardBlock(StructBlock):
    heading = CharBlock()
    text = RichTextBlock(features=["bold", "italic", "link"])
    image = ImageBlock(required=False)

    class Meta:
        icon = "form"
        template = "portfolio/blocks/card_block.html"

# add FeaturedPostsBlock:
class FeaturedPostsBlock(StructBlock):
    heading = CharBlock()
    text = RichTextBlock(features=["bold", "italic", "link"], required=False)
    posts = ListBlock(PageChooserBlock(page_type="blog.BlogPage"))

    class Meta:
        icon = "folder-open-inverse"
        template = "portfolio/blocks/featured_posts_block.html"

class PortfolioStreamBlock(BaseStreamBlock):
    # delete the pass statement

    card = CardBlock(group="Sections")
    featured_posts = FeaturedPostsBlock(group="Sections")