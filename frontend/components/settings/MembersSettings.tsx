'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/stores/authStore';
import { ROLE_LABELS, ROLES } from '@/lib/permissions';
import { authService } from '@/services/auth/authService';
import { apiClient } from '@/services/api/client';
import { toast } from '@/components/ui/Toaster';
import { UserPlus, Mail, MoreVertical, Search, Loader2, X, Clock, CheckCircle2, XCircle, Send } from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';

interface Member {
  id: number;
  full_name: string;
  email: string;
  roles: string[];
  is_active: boolean;
  department_id: number | null;
  position: string | null;
}

interface Invitation {
  id: number;
  email: string;
  role_name: string | null;
  status: string;
  expires_at: string;
  created_at: string;
}

const ASSIGNABLE_ROLES = [
  ROLES.VIEWER, ROLES.DATA_ANALYST, ROLES.RESEARCHER, ROLES.DATA_ENTRY_OFFICER,
  ROLES.DEPT_MANAGER, ROLES.ORG_ADMIN,
];

export function MembersSettings() {
  const { hasPermission } = useAuthStore();
  const canManage = hasPermission('users.manage') || hasPermission('users.create');
  const canEdit = hasPermission('users.edit');

  const [members, setMembers] = useState<Member[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');
  const [inviteDept, setInviteDept] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [departments, setDepartments] = useState<{ id: number; name: string }[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [usersRes, invRes] = await Promise.all([
        apiClient.get<{ users: Member[]; total: number }>('/api/users?page=1&page_size=100'),
        authService.listInvitations().catch(() => []),
      ]);
      setMembers(usersRes.users || []);
      setInvitations(invRes as Invitation[]);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    apiClient.get<{ id: number; name: string }[]>('/api/departments').then(setDepartments).catch(() => {});
  }, [loadData]);

  const filteredMembers = members.filter((m) => {
    const matchesSearch =
      !search ||
      m.full_name.toLowerCase().includes(search.toLowerCase()) ||
      m.email.toLowerCase().includes(search.toLowerCase());
    const matchesRole = !roleFilter || m.roles.includes(roleFilter);
    return matchesSearch && matchesRole;
  });

  const handleInvite = async () => {
    if (!inviteEmail) return;
    setSubmitting(true);
    try {
      await authService.sendInvitation({
        email: inviteEmail,
        role_name: inviteRole,
        department_id: inviteDept ? Number(inviteDept) : undefined,
      });
      toast.success(`Invitation sent to ${inviteEmail}`);
      setShowInvite(false);
      setInviteEmail('');
      setInviteRole('viewer');
      setInviteDept('');
      loadData();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to send invitation';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    setActionLoading(userId);
    try {
      await apiClient.post(`/api/users/${userId}/roles`, [newRole]);
      toast.success('Role updated');
      loadData();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update role';
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleSuspend = async (userId: number, currentlyActive: boolean) => {
    setActionLoading(userId);
    try {
      await apiClient.put(`/api/users/${userId}`, { is_active: !currentlyActive });
      toast.success(currentlyActive ? 'User suspended' : 'User reactivated');
      loadData();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update user';
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRevokeInvitation = async (invitationId: number) => {
    try {
      await authService.revokeInvitation(invitationId);
      toast.success('Invitation revoked');
      loadData();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to revoke invitation';
      toast.error(msg);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary" className="text-xs"><Clock className="mr-1 h-3 w-3" /> Pending</Badge>;
      case 'accepted':
        return <Badge variant="default" className="text-xs"><CheckCircle2 className="mr-1 h-3 w-3" /> Accepted</Badge>;
      case 'revoked':
        return <Badge variant="destructive" className="text-xs"><XCircle className="mr-1 h-3 w-3" /> Revoked</Badge>;
      case 'expired':
        return <Badge variant="destructive" className="text-xs"><XCircle className="mr-1 h-3 w-3" /> Expired</Badge>;
      default:
        return <Badge variant="secondary" className="text-xs">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Members Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Members</CardTitle>
              <CardDescription>Manage users in your organization</CardDescription>
            </div>
            {canManage && (
              <Button onClick={() => setShowInvite(!showInvite)}>
                <UserPlus className="mr-2 h-4 w-4" />
                Invite Member
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Invite form */}
          {showInvite && (
            <div className="mb-4 space-y-3 rounded-lg border p-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="invite-email">Email Address</Label>
                  <Input id="invite-email" type="email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} placeholder="colleague@company.com" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-role">Role</Label>
                  <Select id="invite-role" value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
                    {ASSIGNABLE_ROLES.map((role) => (
                      <option key={role} value={role}>{ROLE_LABELS[role]}</option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-dept">Department (optional)</Label>
                  <Select id="invite-dept" value={inviteDept} onChange={(e) => setInviteDept(e.target.value)}>
                    <option value="">No department</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </Select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleInvite} disabled={submitting}>
                  {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                  Send Invitation
                </Button>
                <Button variant="outline" onClick={() => setShowInvite(false)}>Cancel</Button>
              </div>
              <p className="text-xs text-muted-foreground">
                The invitee will receive an email with a link to create their account.
                Super Admin role cannot be assigned via invitations.
              </p>
            </div>
          )}

          {/* Search & filter */}
          <div className="mb-4 flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search by name or email..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <Select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="w-40">
              <option value="">All roles</option>
              {Object.values(ROLES).map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </Select>
          </div>

          {/* Members list */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredMembers.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No members found</p>
          ) : (
            <div className="space-y-2">
              {filteredMembers.map((member) => (
                <div key={member.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                      {member.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{member.full_name}</p>
                      <p className="text-xs text-muted-foreground">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {member.roles.map((role) => (
                      <Badge key={role} variant="secondary" className="text-xs">
                        {ROLE_LABELS[role] || role}
                      </Badge>
                    ))}
                    <Badge variant={member.is_active ? 'secondary' : 'destructive'} className="text-xs">
                      {member.is_active ? 'Active' : 'Suspended'}
                    </Badge>
                    {canEdit && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" disabled={actionLoading === member.id}>
                            {actionLoading === member.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <MoreVertical className="h-4 w-4" />}
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">Change Role</p>
                          {ASSIGNABLE_ROLES.map((role) => (
                            <DropdownMenuItem key={role} onClick={() => handleRoleChange(member.id, role)}>
                              {ROLE_LABELS[role]}
                            </DropdownMenuItem>
                          ))}
                          <div className="my-1 border-t" />
                          <DropdownMenuItem onClick={() => handleToggleSuspend(member.id, member.is_active)}>
                            {member.is_active ? 'Suspend User' : 'Reactivate User'}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pending Invitations Card */}
      {canManage && invitations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Pending Invitations</CardTitle>
            <CardDescription>Track and manage sent invitations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {invitations.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
                      <Mail className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{inv.email}</p>
                      <p className="text-xs text-muted-foreground">
                        {inv.role_name ? ROLE_LABELS[inv.role_name] || inv.role_name : 'No role'}
                        {' · '}
                        Expires {new Date(inv.expires_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {getStatusBadge(inv.status)}
                    {inv.status === 'pending' && (
                      <Button variant="ghost" size="icon" onClick={() => handleRevokeInvitation(inv.id)}>
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
