/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class ReplacementWizardDialog extends Component {
    static template = "stonia_replacements.ReplacementWizardDialog";
    static components = { Dialog };
    static props = {
        saleOrderId: Number,
        saleOrderName: { type: String, optional: true },
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            step: 1,
            loading: false,
            replacementType: "same_product",
            replacementReasonId: false,
            chargeCustomer: false,
            noChargeReason: "",
            selectedReturnIds: [],
            availableReturns: [],
            replacementReasons: [],
            lines: [],
            totalM2Returned: 0,
            totalM2Replaced: 0,
            totalDifference: 0,
        });

        onWillStart(async () => {
            await this._loadInitialData();
        });
    }

    get dialogTitle() {
        return _t("Reposición de Materiales");
    }

    async _loadInitialData() {
        this.state.loading = true;
        try {
            const returns = await this.orm.call(
                "sale.order", "get_available_returns", [this.props.saleOrderId],
            );
            this.state.availableReturns = returns;
            const reasons = await this.orm.searchRead(
                "stock.replacement.reason",
                [["active", "=", true]],
                ["id", "name", "code"],
                { order: "sequence, id" },
            );
            this.state.replacementReasons = reasons;
        } catch (e) {
            this.notification.add(_t("Error cargando datos: ") + e.message, { type: "danger" });
        }
        this.state.loading = false;
    }

    // =====================================================================
    //  STEP 1 — Type selection (named methods, no inline arrows)
    // =====================================================================
    onSelectTypeSame() { this.state.replacementType = "same_product"; }
    onSelectTypeDifferent() { this.state.replacementType = "different_product"; }
    onSelectTypeRefund() { this.state.replacementType = "refund"; }

    // =====================================================================
    //  STEP 1 — Form inputs
    // =====================================================================
    onReasonChange(ev) {
        this.state.replacementReasonId = parseInt(ev.target.value) || false;
    }

    onChargeChange(ev) {
        this.state.chargeCustomer = ev.target.checked;
    }

    onNoChargeReasonInput(ev) {
        this.state.noChargeReason = ev.target.value;
    }

    // =====================================================================
    //  STEP 1 — Return selection
    // =====================================================================

    /**
     * Read return id from data-return-id attribute on the card element.
     * We walk up the DOM from the click target to find the card.
     */
    onReturnCardClick(ev) {
        const card = ev.currentTarget;
        const returnId = parseInt(card.dataset.returnId);
        if (!returnId) return;
        this.toggleReturn(returnId);
    }

    toggleReturn(returnId) {
        const idx = this.state.selectedReturnIds.indexOf(returnId);
        if (idx >= 0) {
            this.state.selectedReturnIds.splice(idx, 1);
        } else {
            this.state.selectedReturnIds.push(returnId);
        }
    }

    isReturnSelected(returnId) {
        return this.state.selectedReturnIds.includes(returnId);
    }

    selectAllReturns() {
        if (this.state.selectedReturnIds.length === this.state.availableReturns.length) {
            this.state.selectedReturnIds = [];
        } else {
            this.state.selectedReturnIds = this.state.availableReturns.map((r) => r.id);
        }
    }

    get allReturnsSelected() {
        return this.state.availableReturns.length > 0 &&
            this.state.selectedReturnIds.length === this.state.availableReturns.length;
    }

    onCancel() {
        this.props.close();
    }

    // =====================================================================
    //  Navigation
    // =====================================================================
    get canGoStep2() {
        return (
            this.state.selectedReturnIds.length > 0 &&
            this.state.replacementReasonId &&
            (this.state.chargeCustomer || this.state.noChargeReason.trim())
        );
    }

    get canGoStep3() {
        return this.state.lines.some((l) => l.m2ToReplace > 0);
    }

    async goToStep2() {
        if (!this.canGoStep2) return;
        this.state.loading = true;
        try {
            const linesData = await this.orm.call(
                "sale.order", "get_return_lines_for_replacement",
                [this.props.saleOrderId, this.state.selectedReturnIds],
            );
            this.state.lines = linesData.map((l) => ({
                ...l,
                replacementProductId: this.state.replacementType === "same_product" ? l.productId : false,
                replacementProductName: this.state.replacementType === "same_product" ? l.productName : "",
                m2ToReplace: this.state.replacementType === "refund" ? 0 : l.m2Returned,
                replacementUnitPrice: this.state.replacementType === "same_product" ? l.originalUnitPrice : 0,
            }));
            this._recalcTotals();
            this.state.step = 2;
        } catch (e) {
            this.notification.add(_t("Error cargando líneas: ") + e.message, { type: "danger" });
        }
        this.state.loading = false;
    }

    goToStep3() {
        if (!this.canGoStep3) return;
        this._recalcTotals();
        this.state.step = 3;
    }

    goBackTo1() { this.state.step = 1; }
    goBackTo2() { this.state.step = 2; }

    // =====================================================================
    //  STEP 2 — Line editing via data-line-index attribute
    // =====================================================================
    onLineM2ChangeFromEvent(ev) {
        const index = parseInt(ev.target.dataset.lineIndex);
        this.state.lines[index].m2ToReplace = parseFloat(ev.target.value) || 0;
        this._recalcTotals();
    }

    onLinePriceChangeFromEvent(ev) {
        const index = parseInt(ev.target.dataset.lineIndex);
        this.state.lines[index].replacementUnitPrice = parseFloat(ev.target.value) || 0;
        this._recalcTotals();
    }

    async onLineProductChangeFromEvent(ev) {
        const index = parseInt(ev.target.dataset.lineIndex);
        const productId = parseInt(ev.target.value) || false;
        if (productId) {
            const products = await this.orm.read("product.product", [productId], ["display_name", "list_price"]);
            if (products.length) {
                this.state.lines[index].replacementProductId = productId;
                this.state.lines[index].replacementProductName = products[0].display_name;
                this.state.lines[index].replacementUnitPrice = products[0].list_price;
            }
        }
        this._recalcTotals();
    }

    _recalcTotals() {
        let totalReturned = 0, totalReplaced = 0, totalDiff = 0;
        for (const line of this.state.lines) {
            totalReturned += line.m2Returned;
            totalReplaced += line.m2ToReplace;
            totalDiff += (line.m2ToReplace * line.replacementUnitPrice) - (line.m2Returned * line.originalUnitPrice);
        }
        this.state.totalM2Returned = totalReturned;
        this.state.totalM2Replaced = totalReplaced;
        this.state.totalDifference = totalDiff;
    }

    // =====================================================================
    //  Computed helpers
    // =====================================================================
    get replacementTypeLabel() {
        return {
            same_product: "Reposición mismo producto",
            different_product: "Cambio a otro producto",
            refund: "Devolución de dinero",
        }[this.state.replacementType] || "";
    }

    get reasonLabel() {
        const r = this.state.replacementReasons.find((x) => x.id === this.state.replacementReasonId);
        return r ? r.name : "";
    }

    get isRefund() { return this.state.replacementType === "refund"; }

    formatCurrency(val) { return "$" + (val || 0).toFixed(2); }
    formatM2(val) { return (val || 0).toFixed(2) + " m²"; }

    // =====================================================================
    //  Submit
    // =====================================================================
    async onConfirm() {
        this.state.loading = true;
        try {
            const payload = {
                sale_order_id: this.props.saleOrderId,
                replacement_type: this.state.replacementType,
                replacement_reason_id: this.state.replacementReasonId,
                charge_difference: this.state.chargeCustomer,
                no_charge_reason: this.state.noChargeReason,
                return_picking_ids: this.state.selectedReturnIds,
                lines: this.state.lines.map((l) => ({
                    product_id: l.productId,
                    replacement_product_id: l.replacementProductId || l.productId,
                    lot_id: l.lotId,
                    m2_returned: l.m2Returned,
                    m2_to_replace: l.m2ToReplace,
                    original_unit_price: l.originalUnitPrice,
                    replacement_unit_price: l.replacementUnitPrice,
                    move_id: l.moveId,
                    sale_line_id: l.saleLineId,
                })),
            };
            const result = await this.orm.call(
                "sale.order", "create_replacement_from_wizard",
                [this.props.saleOrderId, payload],
            );
            this.notification.add(_t("Reposición creada exitosamente"), { type: "success" });
            this.props.close();
            if (result && result.replacement_id) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: "sale.replacement.order",
                    res_id: result.replacement_id,
                    views: [[false, "form"]],
                    target: "current",
                });
            }
        } catch (e) {
            this.notification.add(_t("Error: ") + (e.data?.message || e.message), { type: "danger", sticky: true });
        }
        this.state.loading = false;
    }
}