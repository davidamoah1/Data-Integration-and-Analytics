'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { RouteGuard } from '@/components/auth/RouteGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CheckSquare, Clock, CheckCircle2 } from 'lucide-react';

interface Task {
  id: number;
  title: string;
  status: 'pending' | 'in_progress' | 'completed';
  due_date?: string;
  priority: 'low' | 'medium' | 'high';
}

export default function AssignedTasksPage() {
  return (
    <RouteGuard roles={['data_entry_officer', 'dept_officer', 'dept_manager', 'org_admin', 'org_owner']}>
      <AssignedTasksContent />
    </RouteGuard>
  );
}

function AssignedTasksContent() {
  const { user } = useAuthStore();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  const pending = tasks.filter((t) => t.status === 'pending');
  const inProgress = tasks.filter((t) => t.status === 'in_progress');
  const completed = tasks.filter((t) => t.status === 'completed');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <CheckSquare className="h-6 w-6" />
          Assigned Tasks
        </h1>
        <p className="mt-1 text-muted-foreground">
          Your assigned data capture and validation tasks.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="text-2xl font-bold">{pending.length}</p>
            </div>
            <Clock className="h-8 w-8 text-amber-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">In Progress</p>
              <p className="text-2xl font-bold">{inProgress.length}</p>
            </div>
            <CheckSquare className="h-8 w-8 text-blue-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold">{completed.length}</p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-green-500" />
          </CardContent>
        </Card>
      </div>

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading tasks...</div>
      ) : tasks.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <CheckSquare className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-lg font-medium">No tasks assigned</p>
            <p className="mt-1 text-sm text-muted-foreground">
              You have no pending tasks. New assignments will appear here.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Task List</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <p className="font-medium">{task.title}</p>
                    {task.due_date && (
                      <p className="text-xs text-muted-foreground">Due: {task.due_date}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        task.priority === 'high'
                          ? 'destructive'
                          : task.priority === 'medium'
                            ? 'warning'
                            : 'default'
                      }
                    >
                      {task.priority}
                    </Badge>
                    <Badge
                      variant={
                        task.status === 'completed'
                          ? 'success'
                          : task.status === 'in_progress'
                            ? 'warning'
                            : 'default'
                      }
                    >
                      {task.status.replace('_', ' ')}
                    </Badge>
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
