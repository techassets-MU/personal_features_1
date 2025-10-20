/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

// console.warn("[price-zero-check] module loaded");

// Muestra una confirmación al validar pago si existen líneas con precio unitario 0.0
patch(PaymentScreen.prototype, {
    async _isOrderValid(isForceValidate) {
        // Ejecutar primero las validaciones estándar de Odoo
        const baseValid = await super._isOrderValid(...arguments);
        if (!baseValid) {
            return false;
        }

        const order = this.currentOrder;
        if (!order) {
            return false;
        }

        const decimals = this.pos.currency?.decimal_places ?? 2;
        const EPS = 1 / Math.pow(10, decimals + 1);
        const isZero = (v) => Math.abs(Number(v || 0)) < EPS;
        const lines = order.get_orderlines?.() || [];

        // console.warn("[price-zero-check] start _isOrderValid", {
        //     orderId: order.id,
        //     linesCount: lines.length,
        //     orderTotal: typeof order.get_total_with_tax === "function" ? order.get_total_with_tax() : undefined,
        // });

        const hasZeroPrice = lines.some((line, idx) => {
            const qty = typeof line.get_quantity === "function" ? line.get_quantity() : undefined;
            const unit = typeof line.get_unit_price === "function" ? line.get_unit_price() : undefined;
            const subtotal =
                typeof line.get_display_price === "function" ? line.get_display_price() : (unit || 0) * (qty || 0);
            const productName = line.get_product?.()?.display_name || line.product_id?.display_name;

            const result = isZero(subtotal);

            // console.warn("[price-zero-check] line", idx, productName, {
            //     qty,
            //     unit,
            //     subtotal,
            //     zeroSubtotal: result,
            // });
            return result;
        });

        if (hasZeroPrice) {
            // console.warn("[price-zero-check] zero-price detected, asking confirmation");
            const confirmed = await ask(this.dialog, {
                title: _t("Precio S/ 0.0"),
                body: _t("El producto tiene precio S/ 0.0. ¿Desea continuar?"),
                confirmLabel: _t("Continuar"),
                cancelLabel: _t("Cancelar"),
            });
            // console.warn("[price-zero-check] confirm result:", confirmed);
            if (!confirmed) {
                // console.warn("[price-zero-check] blocking validation due to cancel");
                return false;
            }
        }

        return true;
    },
});


