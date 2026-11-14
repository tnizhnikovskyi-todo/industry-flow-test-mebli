import { ErrorDialog } from "@web/core/errors/error_dialogs";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { TdSupportDialog } from "../support_dialog/support_dialog";

/** ErrorDialog and its subclasses (ClientErrorDialog, NetworkErrorDialog, RPCErrorDialog) share the template
 *  web.ErrorDialog and this prototype (web/static/src/core/errors/error_dialogs.js). */
patch(ErrorDialog.prototype, {
    setup() {
        super.setup(...arguments);
        this.tdDialog = useService("dialog");
    },
    get tdCanSendToSupport() {
        return user.isInternalUser;
    },
    onTdSendToSupport() {
        this.tdDialog.add(TdSupportDialog, {
            error: {
                title: (this.title || this.constructor.title || "").toString(),
                name: this.props.name || "",
                message: this.props.message || "",
                contextDetails: this.contextDetails || "",
                traceback: this.traceback || this.props.traceback || "",
            },
        });
    },
});
