import { Component, onWillStart, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

const MODEL = "td.support.request";

function readFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

/**
 * Request to the ToDo support: subject, description, attachments (or a screenshot pasted with Ctrl+V), contact,
 * consent. Everything that will be sent is shown before the user confirms.
 * Opened from the systray icon and from the error dialogs (props.error).
 */
export class TdSupportDialog extends Component {
    static template = "td_support.SupportDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        error: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        const error = this.props.error;
        this.state = useState({
            subject: error ? `${_t("Error")}: ${error.title || error.name || ""}`.trim() : "",
            description: "",
            contact: "",
            consent: false,
            files: [],
            context: {},
            showDetails: Boolean(error),
            sending: false,
            message: "",
        });
        this.pageUrl = browser.location.href;
        this.trace = error
            ? [error.title, error.name, error.message, error.contextDetails, error.traceback]
                  .filter(Boolean)
                  .join("\n\n")
            : "";
        onWillStart(async () => {
            this.state.context = await this.orm.call(MODEL, "td_get_context", []);
            this.state.contact = this.state.context.contact || "";
        });
    }

    get title() {
        return this.props.error ? _t("Send to ToDo Support") : _t("ToDo Support");
    }

    get canSend() {
        return this.state.subject.trim() && this.state.consent && !this.state.sending;
    }

    get totalMb() {
        const bytes = this.state.files.reduce((sum, f) => sum + f.size, 0);
        return (bytes / 1024 / 1024).toFixed(1);
    }

    async addFiles(fileList) {
        const ctx = this.state.context;
        for (const file of fileList) {
            if (this.state.files.length >= (ctx.max_files || 5)) {
                this.state.message = _t("No more than %s files can be attached.", ctx.max_files || 5);
                break;
            }
            const datas = await readFile(file);
            this.state.files.push({
                name: file.name || `screenshot-${this.state.files.length + 1}.png`,
                mimetype: file.type,
                size: file.size,
                datas,
            });
        }
    }

    onFileChange(ev) {
        this.addFiles([...ev.target.files]);
        ev.target.value = "";
    }

    onPaste(ev) {
        const files = [...(ev.clipboardData?.files || [])].filter((f) => f.type.startsWith("image/"));
        if (files.length) {
            ev.preventDefault();
            this.addFiles(files);
        }
    }

    removeFile(index) {
        this.state.files.splice(index, 1);
    }

    openHistory() {
        this.action.doAction("td_support.action_td_support_request");
        this.props.close();
    }

    async send() {
        if (!this.canSend) {
            return;
        }
        this.state.sending = true;
        this.state.message = "";
        try {
            const result = await this.orm.call(MODEL, "td_submit", [
                {
                    subject: this.state.subject,
                    description: this.state.description,
                    contact: this.state.contact,
                    consent: this.state.consent,
                    kind: this.props.error ? "error" : "manual",
                    trace: this.trace,
                    page_url: this.pageUrl,
                    attachments: this.state.files.map(({ name, mimetype, datas }) => ({ name, mimetype, datas })),
                },
            ]);
            if (result.state === "failed") {
                this.notification.add(
                    _t("Request %s is saved but not sent: %s", result.name, result.failure_reason),
                    { type: "warning", sticky: true }
                );
            } else {
                this.notification.add(_t("Request %s is sent to the ToDo support.", result.name), {
                    type: "success",
                });
            }
            this.props.close();
        } catch (e) {
            this.state.message = e.data?.message || e.message || String(e);
        } finally {
            this.state.sending = false;
        }
    }
}
