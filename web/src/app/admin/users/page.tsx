import { PageHeader } from "@/components/shared/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { api } from "@/lib/api";

export default async function UsersPage() {
  const users = await api.getUsers();
  return (
    <div>
      <div className="flex items-center justify-between">
        <PageHeader title="Users" subtitle="Manage access across candidate, recruiter, and admin roles." />
        <Button>Invite user</Button>
      </div>
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="p-3 font-medium">Name</th>
                  <th className="p-3 font-medium">Email</th>
                  <th className="p-3 font-medium">Role</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Last active</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b last:border-0">
                    <td className="p-3 font-medium">{u.name}</td>
                    <td className="p-3 text-muted-foreground">{u.email}</td>
                    <td className="p-3"><Badge variant="secondary" className="capitalize">{u.role}</Badge></td>
                    <td className="p-3"><StatusBadge status={u.status} /></td>
                    <td className="p-3 text-muted-foreground">{u.lastActive === "—" ? "—" : formatDate(u.lastActive)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
