frappe.pages['sales-order-financia'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Sales Order Financial Overview",
        single_column: true,
    });

    const styleId = "so-financia-report-style";
    if (!document.getElementById(styleId)) {
        const style = document.createElement("style");
        style.id = styleId;
        style.textContent = `
            .sofr-root { max-width: 1320px; margin: 0 auto; }
            .sofr-toolbar { display:flex; gap:12px; align-items:flex-end; flex-wrap:wrap; margin-bottom:16px; }
            .sofr-so-field { min-width: 360px; flex: 1 1 420px; max-width: 560px; }
            .sofr-toolbar .btn { height: 34px; }
            .sofr-toolbar .frappe-control { margin-bottom: 0; }
            .sofr-toolbar .form-group { margin-bottom: 0; }
            .sofr-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-bottom:18px; }
            .sofr-card { border:1px solid #ddd; border-radius:10px; padding:12px; background:#fff; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
            .sofr-card .k { color:#6b7280; font-size:12px; }
            .sofr-card .v { font-size:20px; font-weight:700; margin-top:2px; }
            .sofr-panel { margin-bottom:18px; border:1px solid #e5e7eb; border-radius:10px; background:#fff; }
            .sofr-panel-head { padding:10px 12px; border-bottom:1px solid #eef0f2; font-weight:600; background:#fafafa; }
            .sofr-panel-body { padding:10px 12px; }
            .sofr-meta { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:8px 14px; }
            .sofr-table-wrap { overflow:auto; }
            .sofr-table { width:100%; border-collapse: collapse; font-size: 12px; }
            .sofr-table th { white-space: nowrap; background:#f8fafc; border-bottom:1px solid #dbe1e8; padding:8px; text-align:left; position: sticky; top: 0; }
            .sofr-table td { border-bottom:1px solid #edf0f2; padding:8px; vertical-align: top; }
            .sofr-empty { color:#6b7280; padding:8px 0; }
            .sofr-print-header, .sofr-print-footer { display:none; }
            @media print {
                .layout-side-section, .navbar, .page-head, .sofr-no-print { display: none !important; }
                .layout-main-section { margin-left: 0 !important; width: 100% !important; }
                .sofr-root { max-width: 100% !important; }
                .sofr-panel { page-break-inside: avoid; }
                .sofr-table th { position: static !important; }
                .sofr-print-header, .sofr-print-footer {
                    display:block !important;
                    width: 100%;
                    color: #111827;
                }
                .sofr-print-header {
                    border-bottom: 1px solid #d1d5db;
                    margin-bottom: 10px;
                    padding-bottom: 8px;
                }
                .sofr-print-title { font-size: 18px; font-weight: 700; }
                .sofr-print-meta { font-size: 12px; color: #4b5563; margin-top: 2px; }
                .sofr-print-footer {
                    position: fixed;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    border-top: 1px solid #d1d5db;
                    padding-top: 6px;
                    font-size: 11px;
                    color: #4b5563;
                    background: #fff;
                }
                #sofr_print_area { padding-bottom: 28px; }
            }
        `;
        document.head.appendChild(style);
    }

    const $root = $(
        `<div class="sofr-root" id="sofr_print_area">
            <div class="sofr-print-header">
                <div class="sofr-print-title">Sales Order Financial Overview</div>
                <div class="sofr-print-meta" id="sofr_print_meta"></div>
            </div>

            <div class="sofr-toolbar sofr-no-print">
                <div id="sales_order_field" class="sofr-so-field"></div>
                <button class="btn btn-primary" id="load_data_btn">Load Data</button>
                <button class="btn btn-default" id="print_btn">Print</button>
            </div>

            <div id="summary_cards" class="sofr-grid"></div>

            <div class="sofr-panel">
                <div class="sofr-panel-head">Sales Order Details</div>
                <div class="sofr-panel-body" id="sales_order_info"></div>
            </div>

            <div class="sofr-panel">
                <div class="sofr-panel-head">Sales Order Items</div>
                <div class="sofr-panel-body" id="items_table"></div>
            </div>

            <div class="sofr-panel">
                <div class="sofr-panel-head">Advance Payments (Against Sales Order)</div>
                <div class="sofr-panel-body" id="advance_table"></div>
            </div>

            <div class="sofr-panel">
                <div class="sofr-panel-head">Invoices Created From This Sales Order</div>
                <div class="sofr-panel-body" id="invoice_table"></div>
            </div>

            <div class="sofr-panel">
                <div class="sofr-panel-head">Payments Received Against Invoices/Payment Allocated from Advances</div>
                <div class="sofr-panel-body" id="invoice_payment_table"></div>
            </div>

            <div class="sofr-panel">
                <div class="sofr-panel-head">Refund Requests Against Sales Order</div>
                <div class="sofr-panel-body" id="refund_request_table"></div>
            </div>

            <div class="sofr-panel">
                <div class="sofr-panel-head">Credit Notes / Sales Returns / Journal Entries Against Refund</div>
                <div class="sofr-panel-body" id="refund_credit_note_table"></div>
            </div>

            <div class="sofr-print-footer">
                <div id="sofr_print_footer_text"></div>
            </div>
        </div>`
    );

    $(page.body).append($root);

    const sales_order_field = frappe.ui.form.make_control({
        parent: $root.find("#sales_order_field"),
        df: {
            label: "Sales Order",
            fieldname: "sales_order",
            fieldtype: "Link",
            options: "Sales Order",
            reqd: 1,
        },
        render_input: true,
    });

    function fmtCurrency(value, currency) {
        return format_currency(value || 0, currency || "INR");
    }

    function getPaymentDocType(row) {
        if (row.payment_source === "Journal Entry") return "journal-entry";
        if (row.payment_source === "Sales Order Advance Allocation") return "sales-order";
        return ((row.payment_entry || "").startsWith("JV-") || (row.payment_entry || "").startsWith("ACC-JV-"))
            ? "journal-entry"
            : "payment-entry";
    }

    function makeTable(rows, columns, $container, emptyMessage) {
        if (!rows || !rows.length) {
            $container.html(`<div class="sofr-empty">${emptyMessage}</div>`);
            return;
        }

        let head = columns.map((c) => `<th>${c.label}</th>`).join("");
        let body = rows.map((row) => {
            const tds = columns.map((c) => `<td>${c.formatter ? c.formatter(row[c.fieldname], row) : (row[c.fieldname] ?? "")}</td>`).join("");
            return `<tr>${tds}</tr>`;
        }).join("");

        $container.html(`<div class="sofr-table-wrap"><table class="sofr-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`);
    }

    function renderData(payload) {
        const so = payload.sales_order || {};
        const totals = payload.totals || {};
        const printedAt = frappe.datetime.str_to_user(frappe.datetime.now_datetime());
        $root.find("#sofr_print_meta").text(`Sales Order: ${so.name || "N/A"} | Printed: ${printedAt}`);
        $root.find("#sofr_print_footer_text").text(`Generated from Warrior/Shoption ERP | ${printedAt}`);

        const summary = [
            { label: "SO Total", value: fmtCurrency(totals.sales_order_total, so.currency) },
            { label: "SO Advance Paid", value: fmtCurrency(totals.sales_order_advance_paid, so.currency) },
            { label: "Invoice Total", value: fmtCurrency(totals.invoice_total, so.currency) },
            { label: "Invoice Outstanding", value: fmtCurrency(totals.invoice_outstanding_total, so.currency) },
            { label: "Invoice Payments Allocated", value: fmtCurrency(totals.invoice_payment_allocated_total, so.currency) },
        ];

        $root.find("#summary_cards").html(
            summary
                .map(
                    (s) =>
                        `<div class="sofr-card">
                            <div class="k">${s.label}</div>
                            <div class="v">${s.value}</div>
                        </div>`
                )
                .join("")
        );

        $root.find("#sales_order_info").html(
            `<div class="sofr-meta">
                <div><strong>Sales Order:</strong> <a href="/app/sales-order/${so.name}" target="_blank">${so.name || "N/A"}</a></div>
                <div><strong>Date:</strong> ${frappe.datetime.str_to_user(so.transaction_date || "N/A")}</div>
                <div><strong>Delivery Date:</strong> ${so.delivery_date ? frappe.datetime.str_to_user(so.delivery_date) : "N/A"}</div>
                <div><strong>Customer ID:</strong> ${so.customer || "N/A"}</div>
                <div><strong>Customer Name:</strong> ${so.customer_name || "N/A"}</div>
                <div><strong>Customer Group:</strong> ${so.customer_group || "N/A"}</div>
                ${(String(so.customer_group || "").toLowerCase() === "dealer") ? `<div><strong>Shop Name:</strong> ${so.shop_name || "N/A"}</div>` : ""}
                <div><strong>Payment Type:</strong> ${so.custom_payment_type || "N/A"}</div>
                <div><strong>Coupon Code:</strong> ${so.custom_coupon_code_for_discount || "N/A"}</div>
                <div><strong>Discount:</strong> ${fmtCurrency(so.discount_amount, so.currency)}</div>
                <div><strong>Coupon Discount:</strong> ${fmtCurrency(so.custom_coupon_discount_amount, so.currency)}</div>
                <div><strong>Dispatch Status:</strong> ${so.custom_dispatch_status || "N/A"}</div>
            </div>`
        );

        makeTable(
            payload.items,
            [
                { label: "SO Item Row", fieldname: "sales_order_item" },
                { label: "Item Code", fieldname: "item_code" },
                { label: "Item Name", fieldname: "item_name" },
               
                { label: "HSN/ASC", fieldname: "gst_hsn_code" },
                { label: "Qty", fieldname: "qty" },
                { label: "Delivered Qty", fieldname: "delivered_qty" },
                { label: "UOM", fieldname: "uom" },
                { label: "Rate", fieldname: "rate", formatter: (v) => fmtCurrency(v, so.currency) },
                { label: "Amount", fieldname: "amount", formatter: (v) => fmtCurrency(v, so.currency) },
                 { label: "Item Tax Template", fieldname: "item_tax_template" },
                { label: "Delivery Date", fieldname: "delivery_date", formatter: (v) => (v ? frappe.datetime.str_to_user(v) : "") },
                { label: "Description", fieldname: "description" },
            ],
            $root.find("#items_table"),
            "No items found for this Sales Order."
        );

        makeTable(
            payload.advance_payments,
            [
                { label: "Source", fieldname: "payment_source", formatter: (v, r) => v || (getPaymentDocType(r) === "journal-entry" ? "Journal Entry" : "Payment Entry") },
                { label: "Payment Entry", fieldname: "payment_entry", formatter: (v, r) => `<a href="/app/${getPaymentDocType(r)}/${v}" target="_blank">${v}</a>` },
                { label: "Posting Date", fieldname: "posting_date", formatter: (v) => frappe.datetime.str_to_user(v) },
                { label: "Mode", fieldname: "mode_of_payment" },
                { label: "From/To", fieldname: "paid_from", formatter: (_, r) => `${r.paid_from || ""} -> ${r.paid_to || ""}` },
                { label: "Allocated", fieldname: "allocated_amount", formatter: (v) => fmtCurrency(v, so.currency) },
                { label: "Reference No", fieldname: "reference_no" },
                { label: "Remark", fieldname: "remark"},
            ],
            $root.find("#advance_table"),
            "No advance payments found for this Sales Order."
        );

        makeTable(
            payload.invoices,
            [
                { label: "Invoice", fieldname: "invoice", formatter: (v) => `<a href="/app/sales-invoice/${v}" target="_blank">${v}</a>` },
                { label: "Date", fieldname: "posting_date", formatter: (v) => frappe.datetime.str_to_user(v) },
                { label: "Customer", fieldname: "customer_name" },
                { label: "Invoice Amount", fieldname: "rounded_total", formatter: (v, r) => fmtCurrency(v || r.grand_total, so.currency) },
                { label: "Outstanding", fieldname: "outstanding_amount", formatter: (v) => fmtCurrency(v, so.currency) },
                { label: "Status", fieldname: "status" },
                { label: "Dispatch Status", fieldname: "custom_dispatch_status" },
                { label: "Pending Stage", fieldname: "pending_stage" },
                                {label: "Is Van Invoice", fieldname: "is_van_invoice"},

                { label: "Stickers", fieldname: "sticker_print_status" },
                { label: "Sticker Logs", fieldname: "sticker_logs_count" },
                { label: "Packing OK", fieldname: "packing_ok_slip", formatter: (v) => (v ? `<a href="/app/packing-ok-slip/${v}" target="_blank">${v}</a>` : "") },
                { label: "Packing Boxes", fieldname: "packing_ok_boxes" },
                { label: "LR", fieldname: "lr_number", formatter: (v) => (v ? `<a href="/app/upload-lr-main/${v}" target="_blank">${v}</a>` : "") },
                { label: "Shipment", fieldname: "shipment", formatter: (v) => (v ? `<a href="/app/shipment/${v}" target="_blank">${v}</a>` : "") },
            ],
            $root.find("#invoice_table"),
            "No invoices found for this Sales Order."
        );

        makeTable(
            payload.invoice_payments,
            [
                { label: "Invoice", fieldname: "invoice", formatter: (v) => `<a href="/app/sales-invoice/${v}" target="_blank">${v}</a>` },
                { label: "Source", fieldname: "payment_source", formatter: (v, r) => v || (getPaymentDocType(r) === "journal-entry" ? "Journal Entry" : "Payment Entry") },
                { label: "Payment Entry", fieldname: "payment_entry", formatter: (v, r) => `<a href="/app/${getPaymentDocType(r)}/${v}" target="_blank">${v}</a>` },
                { label: "Posting Date", fieldname: "posting_date", formatter: (v) => frappe.datetime.str_to_user(v) },
                { label: "Mode", fieldname: "mode_of_payment" },
                { label: "From/To", fieldname: "paid_from", formatter: (_, r) => `${r.paid_from || ""} -> ${r.paid_to || ""}` },
                { label: "Allocated", fieldname: "allocated_amount", formatter: (v) => fmtCurrency(v, so.currency) },
                { label: "Reference No", fieldname: "reference_no" },
                { label: "Reference Date", fieldname: "reference_date", formatter: (v) => (v ? frappe.datetime.str_to_user(v) : "") },
            ],
            $root.find("#invoice_payment_table"),
            "No received payments found against related invoices."
        );

        makeTable(
            payload.refund_requests,
            [
                { label: "Refund Request", fieldname: "name", formatter: (v) => `<a href="/app/refund-request/${v}" target="_blank">${v}</a>` },
                { label: "Created On", fieldname: "created_on", formatter: (v) => (v ? frappe.datetime.str_to_user(v) : "") },
                { label: "Customer", fieldname: "customer_name" },
                { label: "Requested Refund", fieldname: "requested_refund_amount", formatter: (v) => fmtCurrency(v, so.currency) },
                { label: "Paid Amount (SO)", fieldname: "paid_amount", formatter: (v) => fmtCurrency(v, so.currency) },
                { label: "Refund Mode", fieldname: "refund_mode" },
                { label: "Workflow State", fieldname: "workflow_state" },
                { label: "Target Order", fieldname: "target_order", formatter: (v) => (v ? `<a href="/app/sales-order/${v}" target="_blank">${v}</a>` : "") },
                { label: "Paid On", fieldname: "paid_on", formatter: (v) => (v ? frappe.datetime.str_to_user(v) : "") },
                { label: "Credit Note / JE", fieldname: "journal_entry", formatter: (v) => (v ? `<a href="/app/journal-entry/${v}" target="_blank">${v}</a>` : "") },
            ],
            $root.find("#refund_request_table"),
            "No refund requests found against this Sales Order."
        );

        makeTable(
            payload.refund_credit_notes,
            [
                { label: "Type", fieldname: "entry_type" },
                { label: "Refund Request", fieldname: "refund_request", formatter: (v) => `<a href="/app/refund-request/${v}" target="_blank">${v}</a>` },
                { label: "Journal Entry", fieldname: "journal_entry", formatter: (v) => (v ? `<a href="/app/journal-entry/${v}" target="_blank">${v}</a>` : "") },
                { label: "Sales Return / Credit Note", fieldname: "sales_return_invoice", formatter: (v) => (v ? `<a href="/app/sales-invoice/${v}" target="_blank">${v}</a>` : "") },
                { label: "Against Sales Invoice", fieldname: "against_sales_invoice", formatter: (v) => (v ? `<a href="/app/sales-invoice/${v}" target="_blank">${v}</a>` : "") },
                { label: "Posting Date", fieldname: "posting_date", formatter: (v) => (v ? frappe.datetime.str_to_user(v) : "") },
                { label: "Amount", fieldname: "amount", formatter: (v) => fmtCurrency(v, so.currency) },
                { label: "Voucher Type", fieldname: "voucher_type" },
                { label: "Company", fieldname: "company" },
                { label: "Status", fieldname: "status" },
                { label: "Remark", fieldname: "remark" },
            ],
            $root.find("#refund_credit_note_table"),
            "No refund credit notes/sales returns/journal entries found against this Sales Order."
        );
    }

    function loadData() {
        const sales_order = sales_order_field.get_value();
        if (!sales_order) {
            frappe.msgprint("Please select a Sales Order");
            return;
        }

        frappe.call({
            method: "shoption_api.shoption_test_api.page.sales_order_financia.sales_order_financial_overview.get_sales_order_financial_data",
            args: { sales_order },
            freeze: true,
            freeze_message: "Loading Sales Order financial data...",
            callback: function (r) {
                if (r.message) {
                    renderData(r.message);
                }
            },
        });
    }

    $root.find("#load_data_btn").on("click", loadData);
    $root.find("#print_btn").on("click", function () {
        window.print();
    });
}
