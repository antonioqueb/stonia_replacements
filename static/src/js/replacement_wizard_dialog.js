/** @odoo-module **/

import { Component, useState, onWillStart, useRef } from "@odoo/owl";
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
            // Product search state
            productSearchTerm: "",
            productSearchResults: [],
            productSearchLoading: false,
            activeProductSearchIndex: null, // which line index is searching
            // Lot selection state
            activeLotLineIndex: null, // which line index is picking lots
            availableLots: [],
            lotSearchTerm: "",
            lotSearchLoading: false,
        });

        this._productSearchTimeout = null;

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
    //  STEP 1 — Type selection
    // =====================================================================
    onSelectTypeSame() { this.state.replacementType = "same_product"; }
    onSelectTypeDifferent() { this.state.replacementType = "different_product"; }
    onSelectTypeRefund() { this.state.replacementType = "refund"; }

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
        if (this.state.replacementType === "refund") {
            return this.state.lines.length > 0;
        }
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
                // For same_product, pre-fill product but NO lots yet
                replacementProductId: this.state.replacementType === "same_product" ? l.productId : false,
                replacementProductName: this.state.replacementType === "same_product" ? l.productName : "",
                m2ToReplace: this.state.replacementType === "refund" ? 0 : l.m2Returned,
                replacementUnitPrice: this.state.replacementType === "same_product" ? l.originalUnitPrice : 0,
                // NEW: lots for replacement
                replacementLots: [], // [{id, name, quantity}]
                totalLotM2: 0,
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
    //  STEP 2 — Product Search (for "different_product" mode)
    // =====================================================================
    onProductSearchInput(ev) {
        const index = parseInt(ev.target.dataset.lineIndex);
        const term = ev.target.value;
        this.state.productSearchTerm = term;
        this.state.activeProductSearchIndex = index;

        if (this._productSearchTimeout) {
            clearTimeout(this._productSearchTimeout);
        }
        if (term.length < 2) {
            this.state.productSearchResults = [];
            return;
        }
        this._productSearchTimeout = setTimeout(async () => {
            this.state.productSearchLoading = true;
            try {
                const results = await this.orm.call(
                    "sale.order", "search_products_for_replacement",
                    [term, 15],
                );
                // Only update if still on the same search
                if (this.state.activeProductSearchIndex === index) {
                    this.state.productSearchResults = results;
                }
            } catch (e) {
                console.error("Product search error:", e);
            }
            this.state.productSearchLoading = false;
        }, 300);
    }

    onProductSearchFocus(ev) {
        const index = parseInt(ev.target.dataset.lineIndex);
        this.state.activeProductSearchIndex = index;
        // If there's already text, trigger search
        if (ev.target.value && ev.target.value.length >= 2) {
            this.onProductSearchInput(ev);
        }
    }

    onProductSearchBlur() {
        // Delay to allow click on dropdown
        setTimeout(() => {
            this.state.productSearchResults = [];
            this.state.activeProductSearchIndex = null;
        }, 250);
    }

    onSelectProduct(ev) {
        const productId = parseInt(ev.currentTarget.dataset.productId);
        const productName = ev.currentTarget.dataset.productName;
        const productPrice = parseFloat(ev.currentTarget.dataset.productPrice) || 0;
        const index = this.state.activeProductSearchIndex;

        if (index !== null && index >= 0 && index < this.state.lines.length) {
            const line = this.state.lines[index];
            line.replacementProductId = productId;
            line.replacementProductName = productName;
            line.replacementUnitPrice = productPrice;
            // Clear lots when product changes
            line.replacementLots = [];
            line.totalLotM2 = 0;
        }
        this.state.productSearchResults = [];
        this.state.activeProductSearchIndex = null;
        this.state.productSearchTerm = "";
        this._recalcTotals();
    }

    clearProductSelection(ev) {
        const index = parseInt(ev.currentTarget.dataset.lineIndex);
        const line = this.state.lines[index];
        line.replacementProductId = false;
        line.replacementProductName = "";
        line.replacementUnitPrice = 0;
        line.replacementLots = [];
        line.totalLotM2 = 0;
        this._recalcTotals();
    }

    // =====================================================================
    //  STEP 2 — Lot Selection
    // =====================================================================
    async openLotSelector(ev) {
        const index = parseInt(ev.currentTarget.dataset.lineIndex);
        const line = this.state.lines[index];

        if (!line.replacementProductId) {
            this.notification.add(_t("Primero seleccione un producto de reposición"), { type: "warning" });
            return;
        }

        this.state.activeLotLineIndex = index;
        this.state.lotSearchTerm = "";
        this.state.lotSearchLoading = true;

        try {
            // Get already selected lot IDs across all lines for this product
            const excludeIds = this._getExcludedLotIds(index);
            const lots = await this.orm.call(
                "sale.order", "get_available_lots_for_product",
                [line.replacementProductId, excludeIds],
            );
            this.state.availableLots = lots.map((lot) => ({
                ...lot,
                selected: line.replacementLots.some((rl) => rl.id === lot.id),
            }));
        } catch (e) {
            this.notification.add(_t("Error cargando lotes: ") + e.message, { type: "danger" });
        }
        this.state.lotSearchLoading = false;
    }

    _getExcludedLotIds(currentIndex) {
        // Get lot IDs already used in OTHER lines (not current)
        const excluded = [];
        for (let i = 0; i < this.state.lines.length; i++) {
            if (i === currentIndex) continue;
            for (const lot of this.state.lines[i].replacementLots) {
                excluded.push(lot.id);
            }
        }
        return excluded;
    }

    async onLotSearchInput(ev) {
        const term = ev.target.value;
        this.state.lotSearchTerm = term;
        const index = this.state.activeLotLineIndex;
        if (index === null) return;

        const line = this.state.lines[index];
        this.state.lotSearchLoading = true;

        try {
            const excludeIds = this._getExcludedLotIds(index);
            const lots = await this.orm.call(
                "sale.order", "search_lots_for_product",
                [line.replacementProductId, term, excludeIds, 50],
            );
            this.state.availableLots = lots.map((lot) => ({
                ...lot,
                selected: line.replacementLots.some((rl) => rl.id === lot.id),
            }));
        } catch (e) {
            console.error("Lot search error:", e);
        }
        this.state.lotSearchLoading = false;
    }

    toggleLotSelection(ev) {
        const lotId = parseInt(ev.currentTarget.dataset.lotId);
        const index = this.state.activeLotLineIndex;
        if (index === null) return;

        const line = this.state.lines[index];
        const lotInAvailable = this.state.availableLots.find((l) => l.id === lotId);
        if (!lotInAvailable) return;

        const existingIdx = line.replacementLots.findIndex((l) => l.id === lotId);
        if (existingIdx >= 0) {
            // Remove
            line.replacementLots.splice(existingIdx, 1);
            lotInAvailable.selected = false;
        } else {
            // Add
            line.replacementLots.push({
                id: lotInAvailable.id,
                name: lotInAvailable.name,
                quantity: lotInAvailable.quantity,
            });
            lotInAvailable.selected = true;
        }
        // Recalc total lot m2
        line.totalLotM2 = line.replacementLots.reduce((sum, l) => sum + l.quantity, 0);
        line.m2ToReplace = line.totalLotM2;
        this._recalcTotals();
    }

    closeLotSelector() {
        this.state.activeLotLineIndex = null;
        this.state.availableLots = [];
        this.state.lotSearchTerm = "";
    }

    removeLotFromLine(ev) {
        const lineIndex = parseInt(ev.currentTarget.dataset.lineIndex);
        const lotId = parseInt(ev.currentTarget.dataset.lotId);
        const line = this.state.lines[lineIndex];

        const idx = line.replacementLots.findIndex((l) => l.id === lotId);
        if (idx >= 0) {
            line.replacementLots.splice(idx, 1);
            line.totalLotM2 = line.replacementLots.reduce((sum, l) => sum + l.quantity, 0);
            line.m2ToReplace = line.totalLotM2;
            this._recalcTotals();
        }
    }

    // =====================================================================
    //  STEP 2 — Line editing
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
    get isSameProduct() { return this.state.replacementType === "same_product"; }
    get isDifferentProduct() { return this.state.replacementType === "different_product"; }

    get isLotSelectorOpen() { return this.state.activeLotLineIndex !== null; }

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
                    replacement_lot_ids: l.replacementLots.map((rl) => rl.id),
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