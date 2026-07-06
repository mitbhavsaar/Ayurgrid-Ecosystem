import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";

patch(Chatter.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.quickMessage = "";
    },

    async sendQuickMessage() {
        const text = this.state.quickMessage.trim();
        if (!text) return;

        this.state.quickMessage = "";

        // Save record if it is a new unsaved record
        if (this.props.record && !this.props.record.resId) {
            try {
                await this.props.saveRecord?.();
            } catch (e) {
                console.error("Save failed:", e);
                return;
            }
        }

        const resId = this.props.record ? this.props.record.resId : null;
        if (!resId) return;

        try {
            // Post message via standard chatter thread
            await this.orm.call(
                "ag.opd.consultation",
                "action_post_chat_message",
                [resId, text]
            );

            // Reload parent view (updates form fields in real-time)
            await this.reloadParentView();
        } catch (e) {
            console.error("Failed to send quick message:", e);
        }
    },

    onQuickMessageKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendQuickMessage();
        }
    }
});
