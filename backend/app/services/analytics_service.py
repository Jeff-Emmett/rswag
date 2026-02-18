"""Analytics service for admin dashboard."""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, OrderStatus


class AnalyticsService:
    """Service for analytics and reporting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_sales_summary(self, start_date: datetime) -> dict:
        """Get sales summary for the given period."""
        # Total revenue
        revenue_result = await self.db.execute(
            select(func.sum(Order.total))
            .where(
                Order.created_at >= start_date,
                Order.status.in_([
                    OrderStatus.PAID.value,
                    OrderStatus.PROCESSING.value,
                    OrderStatus.SHIPPED.value,
                    OrderStatus.DELIVERED.value,
                ]),
            )
        )
        total_revenue = revenue_result.scalar() or 0

        # Total orders
        orders_result = await self.db.execute(
            select(func.count(Order.id))
            .where(Order.created_at >= start_date)
        )
        total_orders = orders_result.scalar() or 0

        # Completed orders
        completed_result = await self.db.execute(
            select(func.count(Order.id))
            .where(
                Order.created_at >= start_date,
                Order.status.in_([
                    OrderStatus.SHIPPED.value,
                    OrderStatus.DELIVERED.value,
                ]),
            )
        )
        completed_orders = completed_result.scalar() or 0

        # Average order value
        avg_order = total_revenue / total_orders if total_orders > 0 else 0

        return {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "average_order_value": float(avg_order),
            "period_start": start_date.isoformat(),
        }

    async def get_product_performance(
        self,
        start_date: datetime,
        limit: int = 10,
    ) -> list[dict]:
        """Get top performing products."""
        result = await self.db.execute(
            select(
                OrderItem.product_slug,
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_revenue"),
            )
            .join(Order)
            .where(Order.created_at >= start_date)
            .group_by(OrderItem.product_slug, OrderItem.product_name)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            .limit(limit)
        )

        products = []
        for row in result:
            products.append({
                "slug": row.product_slug,
                "name": row.product_name,
                "total_quantity": row.total_quantity,
                "total_revenue": float(row.total_revenue),
            })

        return products
