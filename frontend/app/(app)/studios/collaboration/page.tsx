'use client';

import { useEffect, useState } from 'react';
import { Users, MessageSquare, Share2, History, CheckCircle } from 'lucide-react';
import { collaborationService } from '@/services/studios/studiosService';

export default function CollaborationPage() {
  const [comments, setComments] = useState<any[]>([]);
  const [newComment, setNewComment] = useState('');
  const [resourceType] = useState('workspace');
  const [resourceId] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadComments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadComments() {
    try {
      const res = await collaborationService.listComments(resourceType, resourceId);
      setComments(res.comments || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function addComment() {
    if (!newComment.trim()) return;
    try {
      await collaborationService.addComment({
        resource_type: resourceType,
        resource_id: resourceId,
        content: newComment,
      });
      setNewComment('');
      loadComments();
    } catch {
      // Error handled
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Collaboration</h1>
        <p className="text-gray-600 mt-1">Share, comment, and collaborate on analyses with your team</p>
      </div>

      {/* Features */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { icon: MessageSquare, title: 'Comments', desc: 'Discuss findings with context' },
          { icon: Share2, title: 'Sharing', desc: 'Share with view/edit permissions' },
          { icon: History, title: 'Version Control', desc: 'Track all changes' },
          { icon: Users, title: 'Workspaces', desc: 'Team workspaces' },
        ].map((f) => {
          const Icon = f.icon;
          return (
            <div key={f.title} className="p-4 bg-white rounded-xl border border-gray-200 text-center">
              <Icon size={24} className="mx-auto text-rose-600 mb-2" />
              <h3 className="font-semibold text-sm text-gray-900">{f.title}</h3>
              <p className="text-xs text-gray-500 mt-1">{f.desc}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Comments */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <MessageSquare size={20} className="text-rose-600" />
            Comments
          </h2>

          <div className="mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-500"
                onKeyDown={(e) => e.key === 'Enter' && addComment()}
              />
              <button
                onClick={addComment}
                className="px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700"
              >
                Post
              </button>
            </div>
          </div>

          {loading ? (
            <p className="text-gray-500">Loading comments...</p>
          ) : comments.length === 0 ? (
            <p className="text-gray-500 text-sm">No comments yet. Start the conversation!</p>
          ) : (
            <div className="space-y-3">
              {comments.map((c: any) => (
                <div key={c.id} className={`p-3 rounded-lg border ${c.resolved ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">User #{c.user_id}</span>
                    {c.resolved && <CheckCircle size={16} className="text-green-500" />}
                  </div>
                  <p className="text-sm text-gray-700">{c.content}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {c.created_at && new Date(c.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sharing */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Share2 size={20} className="text-rose-600" />
            Sharing & Permissions
          </h2>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-xl">
              <h3 className="font-medium text-gray-900 mb-2">Permission Levels</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-700">View</span>
                  <span className="text-gray-500">Can see the resource</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">Comment</span>
                  <span className="text-gray-500">Can add comments</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">Edit</span>
                  <span className="text-gray-500">Can modify the resource</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">Admin</span>
                  <span className="text-gray-500">Full control including sharing</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-rose-50 rounded-xl border border-rose-200">
              <h3 className="font-medium text-rose-900 mb-2">Share a Resource</h3>
              <p className="text-sm text-rose-700">
                Select a workspace, dashboard, or presentation to share with team members.
                Set permissions to control what they can do with it.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
