with c as (
  select id, lower(trim(segment)) seg from customers
  where strftime('%Y', joined_at, '+9 hours') = '2024'),
o as (
  select o.id, c.seg from orders o join c on c.id = o.customer_id
  where o.status = 'paid'
    and datetime(o.ordered_at, '+9 hours') >= '2025-07-01' and datetime(o.ordered_at, '+9 hours') < '2025-10-01'),
l as (
  select o.seg, i.order_id, i.product_id,
         i.qty * i.unit_price * (100 - i.discount_pct) / 100 amt,
         i.unit_price * (100 - i.discount_pct) / 100 unit_net
  from order_items i join o on o.id = i.order_id),
r as (select order_id, product_id, sum(qty) q from refunds group by 1, 2)
select seg, sum(amt - coalesce(r.q, 0) * unit_net) net
from l left join r using (order_id, product_id)
group by seg order by net desc limit 3;
