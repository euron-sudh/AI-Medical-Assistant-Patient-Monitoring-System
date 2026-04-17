import { redirect } from "next/navigation";

/** Patient AI Chat was removed from the portal; old bookmarks redirect home. */
export default function PatientChatRemovedPage() {
  redirect("/patient/dashboard");
}
