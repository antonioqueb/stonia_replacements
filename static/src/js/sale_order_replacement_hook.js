/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { ReplacementWizardDialog } from "./replacement_wizard_dialog";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.__replacementDialog = useService("dialog");
    },

    async onWillSaveRecord(record) {
        return super.onWillSaveRecord(...arguments);
    },

    /**
     * Intercept the action_create_replacement button to open OWL dialog instead
     */
    async onButtonClicked(params) {
        if (
            params.name === "action_create_replacement" &&
            this.props.resModel === "sale.order"
        ) {
            const record = this.model.root;
            const saleOrderId = record.resId;
            const saleOrderName = record.data.name || "";

            // First check if there are returns available
            const orm = this.env.services.orm;
            const returns = await orm.call(
                "sale.order",
                "get_available_returns",
                [saleOrderId],
            );

            if (!returns || returns.length === 0) {
                this.env.services.notification.add(
                    "No hay devoluciones validadas para este pedido. Primero debe registrar una devolución.",
                    { title: "Sin devoluciones", type: "warning" },
                );
                return;
            }

            this.__replacementDialog.add(ReplacementWizardDialog, {
                saleOrderId: saleOrderId,
                saleOrderName: saleOrderName,
            });
            return;
        }
        return super.onButtonClicked(...arguments);
    },
});