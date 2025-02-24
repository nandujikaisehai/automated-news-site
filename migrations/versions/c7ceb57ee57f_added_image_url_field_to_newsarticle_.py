"""Added image_url field to NewsArticle model

Revision ID: c7ceb57ee57f
Revises: 
Create Date: 2025-02-24 08:00:58.782057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7ceb57ee57f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('news_article', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('news_article', schema=None) as batch_op:
        batch_op.drop_column('image_url')

    # ### end Alembic commands ###
