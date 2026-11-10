# td_mebli_mrp

Параметричний виріб (номінальні розміри, межі), правила деталей з лінійними формулами і генератор
специфікації (`mrp.bom`) під конкретне замовлення. Не залежить від `sale`.

Генератор: `mrp.bom._td_generate_order_bom(product, dims, selections)`; `dims` — словник
`{'width': мм, 'height': мм, 'depth': мм}`, `selections` — набір `product.attribute.value`.
Специфікація під замовлення має `td_order_bom = True` і не знаходиться стандартним `_bom_find`.
