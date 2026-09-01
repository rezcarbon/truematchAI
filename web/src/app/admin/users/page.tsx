/**
 * Admin Users Management Page - Production Ready
 * Displays users with full CRUD operations, filtering, searching, and pagination
 */
'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/shared/AppShell';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Loader2, Plus, Search, Trash2, Edit2, Mail } from 'lucide-react';
import { adminApi } from '@/lib/api-admin';
import { User, UserRole, UserStatus } from '@/types/admin';
import { formatDate } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const roleColors: Record<UserRole, string> = {
  admin: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  recruiter: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  candidate: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
};

const statusMap: Record<UserStatus, 'success' | 'warning' | 'error' | 'default'> = {
  active: 'success',
  inactive: 'default',
  invited: 'warning',
  suspended: 'error',
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState<UserRole | 'all'>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [inviteEmails, setInviteEmails] = useState('');
  const [inviteRole, setInviteRole] = useState<UserRole>('recruiter');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch users on mount and when filters change
  useEffect(() => {
    fetchUsers();
  }, [page, selectedRole]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getUsers({
        page,
        limit: 10,
        sort: 'createdAt',
        order: 'desc',
      });

      setUsers(response.data);
      setTotalPages(response.pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchUsers();
      return;
    }

    try {
      setLoading(true);
      const results = await adminApi.searchUsers(searchQuery);
      setUsers(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUsers = async () => {
    if (!inviteEmails.trim()) {
      setError('Please enter at least one email');
      return;
    }

    try {
      setIsSubmitting(true);
      const emails = inviteEmails
        .split('\n')
        .map((e) => e.trim())
        .filter((e) => e);

      await adminApi.inviteUsers({
        emails,
        role: inviteRole,
        sendEmail: true,
      });

      setShowCreateDialog(false);
      setInviteEmails('');
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to invite users');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await adminApi.deleteUser(userId);
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    }
  };

  const handleUpdateUser = async (updateData: any) => {
    if (!editingUser) return;

    try {
      setIsSubmitting(true);
      await adminApi.updateUser(editingUser.id, updateData);
      setShowEditDialog(false);
      setEditingUser(null);
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredUsers = selectedRole === 'all' ? users : users.filter((u) => u.role === selectedRole);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="Users"
          subtitle="Manage access across candidate, recruiter, and admin roles."
        />
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Invite Users
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Search and Filter */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="flex gap-2">
          <Input
            placeholder="Search by email or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button variant="outline" size="icon" onClick={handleSearch}>
            <Search className="h-4 w-4" />
          </Button>
        </div>
        <Select value={selectedRole} onValueChange={(v) => setSelectedRole(v as any)}>
          <SelectTrigger>
            <SelectValue placeholder="Filter by role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="recruiter">Recruiter</SelectItem>
            <SelectItem value="candidate">Candidate</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Users Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">No users found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold">Email</th>
                    <th className="px-6 py-3 text-left font-semibold">Name</th>
                    <th className="px-6 py-3 text-left font-semibold">Role</th>
                    <th className="px-6 py-3 text-left font-semibold">Status</th>
                    <th className="px-6 py-3 text-left font-semibold">Last Login</th>
                    <th className="px-6 py-3 text-left font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="border-b hover:bg-muted/30">
                      <td className="px-6 py-3">{user.email}</td>
                      <td className="px-6 py-3">{user.displayName}</td>
                      <td className="px-6 py-3">
                        <Badge className={roleColors[user.role]}>{user.role}</Badge>
                      </td>
                      <td className="px-6 py-3">
                        <StatusBadge status={statusMap[user.status]} text={user.status} />
                      </td>
                      <td className="px-6 py-3 text-muted-foreground">
                        {user.lastLogin ? formatDate(user.lastLogin) : 'Never'}
                      </td>
                      <td className="px-6 py-3">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingUser(user);
                              setShowEditDialog(true);
                            }}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUser(user.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={page === 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Create/Invite Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite Users</DialogTitle>
            <DialogDescription>Add one email per line to invite multiple users at once</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <textarea
              className="min-h-[150px] w-full rounded border bg-background p-3 font-mono text-sm"
              placeholder="user1@example.com&#10;user2@example.com&#10;user3@example.com"
              value={inviteEmails}
              onChange={(e) => setInviteEmails(e.target.value)}
            />
            <Select value={inviteRole} onValueChange={(v) => setInviteRole(v as UserRole)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="recruiter">Recruiter</SelectItem>
                <SelectItem value="candidate">Candidate</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button onClick={handleInviteUsers} disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Send Invites
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      {editingUser && (
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit User</DialogTitle>
              <DialogDescription>Update user information and permissions</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input
                  defaultValue={editingUser.displayName}
                  onChange={(e) =>
                    setEditingUser({ ...editingUser, displayName: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Role</label>
                <Select value={editingUser.role} onValueChange={(v) =>
                  setEditingUser({ ...editingUser, role: v as UserRole })
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="recruiter">Recruiter</SelectItem>
                    <SelectItem value="candidate">Candidate</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Status</label>
                <Select value={editingUser.status} onValueChange={(v) =>
                  setEditingUser({ ...editingUser, status: v as UserStatus })
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setShowEditDialog(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() =>
                    handleUpdateUser({
                      displayName: editingUser.displayName,
                      role: editingUser.role,
                      status: editingUser.status,
                    })
                  }
                  disabled={isSubmitting}
                >
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Save Changes
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
