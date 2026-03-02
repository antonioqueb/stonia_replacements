/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ReplacementWizardDialog } from "./replacement_wizard_dialog";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
    },

    async beforeExecuteActionButton(clickParams) {
        if (
            clickParams.name === "action_create_replacement" &&
            this.props.resModel === "sale.order"
        ) {
            const record = this.model.root;
            const saleOrderId = record.resId;
            const saleOrderName = record.data.name || "";

            const orm = this.env.services.orm;
            const dialog = this.env.services.dialog;
            const notification = this.env.services.notification;

            try {
                const returns = await orm.call(
                    "sale.order",
                    "get_available_returns",
                    [saleOrderId],
                );

                if (!returns || returns.length === 0) {
                    notification.add(
                        "No hay devoluciones validadas para este pedido. Primero debe registrar una devolución.",
                        { title: "Sin devoluciones", type: "warning" },
                    );
                    return false;
                }

                dialog.add(ReplacementWizardDialog, {
                    saleOrderId: saleOrderId,
                    saleOrderName: saleOrderName,
                });
            } catch (e) {
                console.error("Error opening replacement wizard:", e);
                return super.beforeExecuteActionButton(clickParams);
            }
            return false;
        }
        return super.beforeExecuteActionButton(clickParams);
    },
});