# Phase 9.7 — Enterprise Documentation, Knowledge Portal & Learning Center

## Purpose

This document defines the comprehensive Enterprise Documentation, Knowledge Management and Learning Platform for AEDIP, providing world-class documentation, knowledge sharing, and learning capabilities for all stakeholders.

---

## 1. Documentation Architecture

### 1.1 Design Principles

- **Single Source of Truth**: Centralized documentation with version control.
- **Multi-Audience Support**: Content tailored for different user personas.
- **Search-First**: Powerful search capabilities across all content types.
- **AI-Assisted**: AI-powered content generation, summarization, and recommendations.
- **Interactive Learning**: Hands-on tutorials and interactive walkthroughs.
- **Continuous Updates**: Automated documentation updates from code and APIs.
- **Accessibility**: WCAG 2.2 AA compliant documentation interface.

### 1.2 Documentation Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Content Governance & Workflow Layer                           │
│  Approval Workflows · Version Control · Content Review · Audit Trails            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AI-Powered Content Services                                   │
│  Content Generation · Summarization · Translation · Q&A · Recommendations        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Knowledge Management & Search Layer                           │
│  Search Engine · Knowledge Graph · Content Indexing · Analytics                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Learning & Engagement Layer                                   │
│  Courses · Tutorials · Quizzes · Certifications · Progress Tracking             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Content Management & Delivery Layer                          │
│  CMS · Content Types · Templates · Multilingual · Responsive Design             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Core Platform                                      │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Decision Center · Events       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Content Types and Structure

| Content Type | Target Audience | Format | Update Frequency |
|--------------|----------------|--------|------------------|
| **User Guides** | End Users | Markdown + Interactive | Monthly |
| **Admin Guides** | System Admins | Markdown + Screenshots | Quarterly |
| **Developer Guides** | Developers | Markdown + Code Examples | Weekly |
| **API Documentation** | Developers | OpenAPI + Interactive | Auto-generated |
| **Database Documentation** | DBAs, Developers | ER Diagrams + Schema | On schema change |
| **Architecture Docs** | Architects | Diagrams + Markdown | On architecture change |
| **Deployment Guides** | DevOps | Step-by-step + Scripts | On release |
| **ETL Documentation** | Data Engineers | Flow diagrams + Config | On pipeline change |
| **Connector Docs** | Integration Teams | Setup guides + Examples | On connector update |
| **Plugin Documentation** | Plugin Developers | API docs + Tutorials | On plugin release |
| **Dashboard Guides** | Business Users | Interactive tutorials | On dashboard change |
| **Report Documentation** | Analysts | Sample reports + Queries | On report update |
| **Troubleshooting** | All Users | FAQ + Solutions | Continuous |
| **Release Notes** | All Users | Markdown + Changelog | On release |
| **Security Guides** | Security Teams | Policies + Procedures | On policy update |
| **Compliance Guides** | Compliance Teams | Regulations + Controls | On regulation change |

---

## 2. Knowledge Portal Design

### 2.1 Knowledge Portal Architecture

```python
class KnowledgePortal:
    """Enterprise knowledge portal for AEDIP."""
    
    def __init__(self, 
                 content_manager: ContentManager,
                 search_engine: SearchEngine,
                 ai_services: AIServices,
                 user_tracker: UserActivityTracker):
        self.content = content_manager
        self.search = search_engine
        self.ai = ai_services
        self.tracker = user_tracker
    
    async def initialize(self):
        """Initialize knowledge portal."""
        
        # Initialize content manager
        await self.content.initialize()
        
        # Setup search engine
        await self.search.initialize()
        
        # Initialize AI services
        await self.ai.initialize()
        
        # Setup user tracking
        await self.tracker.initialize()
        
        logger.info("Knowledge portal initialized")
    
    async def search_knowledge(self, 
                             query: str,
                             user_context: UserContext) -> SearchResult:
        """Search knowledge base with AI assistance."""
        
        # Enhanced search with AI
        search_result = await self.search.search_with_ai(
            query=query,
            user_context=user_context,
            filters=user_context.filters
        )
        
        # Track search activity
        await self.tracker.track_search(
            user_id=user_context.user_id,
            query=query,
            results_count=len(search_result.articles),
            clicked_articles=search_result.clicked_articles
        )
        
        # Generate AI suggestions
        suggestions = await self.ai.generate_search_suggestions(
            query=query,
            search_result=search_result,
            user_context=user_context
        )
        
        search_result.ai_suggestions = suggestions
        
        return search_result
    
    async def get_article(self, 
                         article_id: str,
                         user_context: UserContext) -> ArticleResponse:
        """Get article with personalization."""
        
        # Get article content
        article = await self.content.get_article(article_id, user_context)
        
        # Generate AI summary
        summary = await self.ai.generate_summary(article.content)
        
        # Get related articles
        related = await self.get_related_articles(article, user_context)
        
        # Track view
        await self.tracker.track_article_view(
            user_id=user_context.user_id,
            article_id=article_id,
            reading_time=article.estimated_reading_time
        )
        
        return ArticleResponse(
            article=article,
            summary=summary,
            related_articles=related,
            user_progress=await self.get_user_progress(user_context.user_id, article_id)
        )
    
    async def get_related_articles(self, 
                                 article: Article,
                                 user_context: UserContext) -> List[Article]:
        """Get related articles using AI."""
        
        # Get related articles based on content similarity
        content_related = await self.search.find_similar_articles(
            article_id=article.id,
            limit=5
        )
        
        # Get related based on user behavior
        behavior_related = await self.tracker.get_behaviorally_related(
            user_id=user_context.user_id,
            article_id=article.id,
            limit=3
        )
        
        # Combine and rank
        related = self.rank_related_articles(
            content_related + behavior_related,
            user_context
        )
        
        return related[:5]  # Return top 5

class ContentManager:
    """Manages content lifecycle and workflows."""
    
    def __init__(self, 
                 storage: ContentStorage,
                 version_control: VersionControl,
                 workflow_engine: WorkflowEngine):
        self.storage = storage
        self.version_control = version_control
        self.workflow = workflow_engine
    
    async def create_article(self, 
                           article: ArticleCreate,
                           author_context: AuthorContext) -> Article:
        """Create new article with workflow."""
        
        # Create article
        new_article = Article(
            id=generate_uuid(),
            title=article.title,
            content=article.content,
            type=article.type,
            category=article.category,
            tags=article.tags,
            author_id=author_context.user_id,
            status='draft',
            created_at=datetime.utcnow()
        )
        
        # Save article
        await self.storage.save_article(new_article)
        
        # Start approval workflow if required
        if article.requires_approval:
            workflow_instance = await self.workflow.start_workflow(
                workflow_type='article_approval',
                entity_id=new_article.id,
                context=article.approval_context
            )
            new_article.workflow_id = workflow_instance.id
        
        # Track creation
        await self.track_content_event(
            event_type='article_created',
            article_id=new_article.id,
            user_id=author_context.user_id
        )
        
        return new_article
    
    async def update_article(self, 
                           article_id: str,
                           updates: ArticleUpdate,
                           author_context: AuthorContext) -> Article:
        """Update article with version control."""
        
        # Get current article
        current_article = await self.storage.get_article(article_id)
        
        # Check permissions
        await self.check_edit_permissions(current_article, author_context)
        
        # Create new version
        new_version = await self.version_control.create_version(
            entity_id=article_id,
            content=current_article.content,
            metadata={
                'updated_by': author_context.user_id,
                'updated_at': datetime.utcnow(),
                'change_summary': updates.change_summary
            }
        )
        
        # Update article
        updated_article = await self.storage.update_article(
            article_id=article_id,
            updates=updates
        )
        
        # Re-index for search
        await self.reindex_article(updated_article)
        
        return updated_article
    
    async def publish_article(self, 
                            article_id: str,
                            publisher_context: PublisherContext) -> Article:
        """Publish article."""
        
        # Get article
        article = await self.storage.get_article(article_id)
        
        # Validate publication requirements
        validation = await self.validate_publication_requirements(article)
        if not validation.is_valid:
            raise PublicationError(validation.errors)
        
        # Update status
        article.status = 'published'
        article.published_at = datetime.utcnow()
        article.published_by = publisher_context.user_id
        
        # Save changes
        await self.storage.save_article(article)
        
        # Notify subscribers
        await self.notify_subscribers(article)
        
        # Update search index
        await self.reindex_article(article)
        
        return article
```

---

## 3. Learning Center Design

### 3.1 Learning Management System

```python
class LearningCenter:
    """Enterprise learning center for AEDIP."""
    
    def __init__(self, 
                 course_manager: CourseManager,
                 tutorial_engine: TutorialEngine,
                 certification_engine: CertificationEngine,
                 progress_tracker: ProgressTracker):
        self.courses = course_manager
        self.tutorials = tutorial_engine
        self.certifications = certification_engine
        self.progress = progress_tracker
    
    async def get_learning_path(self, 
                              user_id: str,
                              learning_goal: LearningGoal) -> LearningPath:
        """Generate personalized learning path."""
        
        # Get user's current skills
        current_skills = await self.progress.get_user_skills(user_id)
        
        # Get required skills for goal
        required_skills = await self.get_required_skills(learning_goal)
        
        # Identify skill gaps
        skill_gaps = self.identify_skill_gaps(current_skills, required_skills)
        
        # Get relevant courses and tutorials
        relevant_content = await self.get_relevant_content(skill_gaps)
        
        # Generate learning path
        learning_path = await self.ai.generate_learning_path(
            user_skills=current_skills,
            skill_gaps=skill_gaps,
            content=relevant_content,
            learning_goal=learning_goal
        )
        
        return learning_path
    
    async def start_course(self, 
                         user_id: str,
                         course_id: str) -> CourseEnrollment:
        """Enroll user in course."""
        
        # Get course
        course = await self.courses.get_course(course_id)
        
        # Check prerequisites
        prerequisites_met = await self.check_prerequisites(user_id, course.prerequisites)
        if not prerequisites_met:
            raise PrerequisiteError("Course prerequisites not met")
        
        # Create enrollment
        enrollment = CourseEnrollment(
            id=generate_uuid(),
            user_id=user_id,
            course_id=course_id,
            status='in_progress',
            enrolled_at=datetime.utcnow(),
            progress=0
        )
        
        # Save enrollment
        await self.progress.save_enrollment(enrollment)
        
        # Track enrollment
        await self.track_learning_event(
            user_id=user_id,
            event_type='course_enrolled',
            course_id=course_id
        )
        
        return enrollment
    
    async def complete_lesson(self, 
                            user_id: str,
                            lesson_id: str,
                            completion_data: LessonCompletion) -> LessonResult:
        """Complete lesson and update progress."""
        
        # Get lesson
        lesson = await self.courses.get_lesson(lesson_id)
        
        # Validate completion
        validation = await self.validate_lesson_completion(lesson, completion_data)
        if not validation.is_valid:
            raise LessonCompletionError(validation.errors)
        
        # Update progress
        await self.progress.update_lesson_progress(
            user_id=user_id,
            lesson_id=lesson_id,
            completion_data=completion_data
        )
        
        # Check if course is completed
        course_progress = await self.progress.get_course_progress(user_id, lesson.course_id)
        if course_progress.is_completed:
            await self.complete_course(user_id, lesson.course_id)
        
        # Award badges if applicable
        await self.check_and_award_badges(user_id, lesson_id)
        
        return LessonResult(
            success=True,
            points_awarded=lesson.points,
            badges_awarded=completion_data.badges_earned,
            next_lesson=await self.get_next_lesson(user_id, lesson.course_id)
        )

class TutorialEngine:
    """Interactive tutorial engine."""
    
    def __init__(self, 
                 interactive_player: InteractivePlayer,
                 lab_manager: LabManager,
                 assessment_engine: AssessmentEngine):
        self.player = interactive_player
        self.labs = lab_manager
        self.assessments = assessment_engine
    
    async def start_interactive_tutorial(self, 
                                       user_id: str,
                                       tutorial_id: str) -> TutorialSession:
        """Start interactive tutorial session."""
        
        # Get tutorial
        tutorial = await self.get_tutorial(tutorial_id)
        
        # Create session
        session = TutorialSession(
            id=generate_uuid(),
            user_id=user_id,
            tutorial_id=tutorial_id,
            current_step=0,
            status='running',
            started_at=datetime.utcnow()
        )
        
        # Setup environment if needed
        if tutorial.requires_lab:
            lab_environment = await self.labs.create_lab_environment(
                user_id=user_id,
                tutorial_id=tutorial_id
            )
            session.lab_environment_id = lab_environment.id
        
        # Save session
        await self.save_session(session)
        
        return session
    
    async def execute_tutorial_step(self, 
                                  session_id: str,
                                  step_input: StepInput) -> StepResult:
        """Execute tutorial step."""
        
        # Get session
        session = await self.get_session(session_id)
        
        # Get current step
        tutorial = await self.get_tutorial(session.tutorial_id)
        current_step = tutorial.steps[session.current_step]
        
        # Execute step based on type
        if current_step.type == 'instruction':
            result = await self.execute_instruction_step(current_step, step_input)
        elif current_step.type == 'interactive':
            result = await self.execute_interactive_step(current_step, step_input, session)
        elif current_step.type == 'lab':
            result = await self.execute_lab_step(current_step, step_input, session)
        elif current_step.type == 'quiz':
            result = await self.execute_quiz_step(current_step, step_input)
        else:
            raise ValueError(f"Unknown step type: {current_step.type}")
        
        # Update session progress
        if result.success and result.completed:
            session.current_step += 1
            if session.current_step >= len(tutorial.steps):
                session.status = 'completed'
                session.completed_at = datetime.utcnow()
            
            await self.save_session(session)
        
        return result
    
    async def execute_interactive_step(self, 
                                     step: TutorialStep,
                                     step_input: StepInput,
                                     session: TutorialSession) -> StepResult:
        """Execute interactive step with live environment."""
        
        # Get lab environment
        lab_env = await self.labs.get_environment(session.lab_environment_id)
        
        # Execute user action in lab
        execution_result = await self.labs.execute_action(
            environment=lab_env,
            action=step_input.action,
            code=step_input.code
        )
        
        # Validate result
        validation = await self.validate_step_result(step, execution_result)
        
        # Provide feedback
        feedback = await self.ai.generate_step_feedback(
            step=step,
            user_input=step_input,
            execution_result=execution_result,
            validation=validation
        )
        
        return StepResult(
            success=validation.is_valid,
            completed=validation.is_valid,
            execution_result=execution_result,
            feedback=feedback,
            hints=await self.generate_hints(step, step_input, validation)
        )
```

---

## 4. Database Schema

### 4.1 Documentation and Knowledge Tables

```sql
CREATE TABLE knowledge_articles (
  id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(512) NOT NULL,
  slug VARCHAR(512) NOT NULL UNIQUE,
  content LONGTEXT NOT NULL,
  content_type ENUM('markdown', 'html', 'json') DEFAULT 'markdown',
  article_type VARCHAR(64) NOT NULL, -- user_guide, admin_guide, developer_guide, api_docs, etc.
  category_id BIGINT,
  status ENUM('draft', 'review', 'approved', 'published', 'archived') DEFAULT 'draft',
  language VARCHAR(10) DEFAULT 'en',
  author_id BIGINT NOT NULL,
  reviewer_id BIGINT,
  published_by BIGINT,
  published_at DATETIME,
  version INT DEFAULT 1,
  parent_article_id VARCHAR(64), -- For translations
  reading_time_minutes INT,
  difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
  target_audience JSON, -- Array of audience types
  prerequisites JSON, -- Array of prerequisite article IDs
  related_articles JSON, -- Array of related article IDs
  metadata JSON, -- Additional metadata
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status),
  idx_type (article_type),
  idx_category (category_id),
  idx_author (author_id),
  idx_published (published_at),
  idx_language (language),
  idx_slug (slug),
  FULLTEXT idx_search (title, content)
) ENGINE=InnoDB;

CREATE TABLE article_versions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  article_id VARCHAR(64) NOT NULL,
  version_number INT NOT NULL,
  title VARCHAR(512) NOT NULL,
  content LONGTEXT NOT NULL,
  change_summary TEXT,
  created_by BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (article_id) REFERENCES knowledge_articles(id),
  INDEX idx_article_version (article_id, version_number),
  idx_created_by (created_by),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE article_categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(256) NOT NULL,
  slug VARCHAR(256) NOT NULL UNIQUE,
  description TEXT,
  parent_category_id BIGINT,
  icon VARCHAR(128),
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_category_id) REFERENCES article_categories(id),
  INDEX idx_parent (parent_category_id),
  idx_active (is_active),
  idx_sort (sort_order)
) ENGINE=InnoDB;

CREATE TABLE article_tags (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL UNIQUE,
  slug VARCHAR(128) NOT NULL UNIQUE,
  description TEXT,
  color VARCHAR(7), -- Hex color code
  usage_count INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_name (name),
  idx_usage (usage_count)
) ENGINE=InnoDB;

CREATE TABLE article_tag_relations (
  article_id VARCHAR(64) NOT NULL,
  tag_id BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (article_id, tag_id),
  FOREIGN KEY (article_id) REFERENCES knowledge_articles(id),
  FOREIGN KEY (tag_id) REFERENCES article_tags(id)
) ENGINE=InnoDB;

CREATE TABLE article_comments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  article_id VARCHAR(64) NOT NULL,
  parent_comment_id BIGINT, -- For threaded comments
  user_id BIGINT NOT NULL,
  content TEXT NOT NULL,
  is_internal BOOLEAN DEFAULT FALSE, -- Internal comments for reviewers
  status ENUM('active', 'hidden', 'deleted') DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (article_id) REFERENCES knowledge_articles(id),
  FOREIGN KEY (parent_comment_id) REFERENCES article_comments(id),
  INDEX idx_article (article_id),
  idx_user (user_id),
  idx_parent (parent_comment_id),
  idx_status (status),
  idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE article_ratings (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  article_id VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL,
  rating TINYINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
  feedback TEXT,
  helpful BOOLEAN, -- Was the article helpful?
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_article_user (article_id, user_id),
  FOREIGN KEY (article_id) REFERENCES knowledge_articles(id),
  INDEX idx_article (article_id),
  idx_rating (rating),
  idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE documentation_sections (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(256) NOT NULL,
  slug VARCHAR(256) NOT NULL UNIQUE,
  description TEXT,
  parent_section_id BIGINT,
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_section_id) REFERENCES documentation_sections(id),
  INDEX idx_parent (parent_section_id),
  idx_active (is_active),
  idx_sort (sort_order)
) ENGINE=InnoDB;

CREATE TABLE tutorials (
  id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(512) NOT NULL,
  description TEXT,
  content LONGTEXT NOT NULL,
  tutorial_type ENUM('interactive', 'video', 'written', 'lab') DEFAULT 'written',
  category_id BIGINT,
  difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
  estimated_duration_minutes INT,
  prerequisites JSON, -- Tutorial IDs or skills
  learning_objectives JSON,
  author_id BIGINT NOT NULL,
  status ENUM('draft', 'review', 'published', 'archived') DEFAULT 'draft',
  published_at DATETIME,
  view_count INT DEFAULT 0,
  completion_count INT DEFAULT 0,
  average_rating DECIMAL(3,2),
  tags JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES article_categories(id),
  INDEX idx_type (tutorial_type),
  idx_difficulty (difficulty_level),
  idx_status (status),
  idx_published (published_at),
  idx_author (author_id),
  FULLTEXT idx_search (title, description, content)
) ENGINE=InnoDB;

CREATE TABLE courses (
  id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(512) NOT NULL,
  description TEXT,
  course_type ENUM('self_paced', 'instructor_led', 'blended') DEFAULT 'self_paced',
  category_id BIGINT,
  difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
  estimated_duration_hours INT,
  prerequisites JSON,
  learning_objectives JSON,
  instructor_id BIGINT,
  status ENUM('draft', 'review', 'published', 'archived') DEFAULT 'draft',
  published_at DATETIME,
  enrollment_count INT DEFAULT 0,
  completion_count INT DEFAULT 0,
  average_rating DECIMAL(3,2),
  price DECIMAL(10,2) DEFAULT 0.00,
  certificate_available BOOLEAN DEFAULT FALSE,
  tags JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES article_categories(id),
  INDEX idx_type (course_type),
  idx_difficulty (difficulty_level),
  idx_status (status),
  idx_instructor (instructor_id),
  idx_published (published_at)
) ENGINE=InnoDB;

CREATE TABLE course_modules (
  id VARCHAR(64) PRIMARY KEY,
  course_id VARCHAR(64) NOT NULL,
  title VARCHAR(512) NOT NULL,
  description TEXT,
  sort_order INT DEFAULT 0,
  is_mandatory BOOLEAN DEFAULT TRUE,
  estimated_duration_minutes INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES courses(id),
  INDEX idx_course (course_id),
  idx_sort (sort_order),
  idx_mandatory (is_mandatory)
) ENGINE=InnoDB;

CREATE TABLE course_lessons (
  id VARCHAR(64) PRIMARY KEY,
  module_id VARCHAR(64) NOT NULL,
  title VARCHAR(512) NOT NULL,
  content LONGTEXT,
  lesson_type ENUM('text', 'video', 'interactive', 'quiz', 'assignment') DEFAULT 'text',
  sort_order INT DEFAULT 0,
  is_mandatory BOOLEAN DEFAULT TRUE,
  estimated_duration_minutes INT,
  video_url VARCHAR(512),
  interactive_content JSON,
  quiz_questions JSON,
  assignment_instructions TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (module_id) REFERENCES course_modules(id),
  INDEX idx_module (module_id),
  idx_type (lesson_type),
  idx_sort (sort_order),
  idx_mandatory (is_mandatory)
) ENGINE=InnoDB;

CREATE TABLE course_enrollments (
  id VARCHAR(64) PRIMARY KEY,
  user_id BIGINT NOT NULL,
  course_id VARCHAR(64) NOT NULL,
  status ENUM('enrolled', 'in_progress', 'completed', 'dropped', 'suspended') DEFAULT 'enrolled',
  progress_percentage DECIMAL(5,2) DEFAULT 0.00,
  enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  started_at DATETIME,
  completed_at DATETIME,
  last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  certificate_issued BOOLEAN DEFAULT FALSE,
  certificate_issued_at DATETIME,
  UNIQUE KEY uniq_user_course (user_id, course_id),
  FOREIGN KEY (course_id) REFERENCES courses(id),
  INDEX idx_user (user_id),
  idx_status (status),
  idx_progress (progress_percentage),
  idx_enrolled (enrolled_at),
  idx_completed (completed_at)
) ENGINE=InnoDB;

CREATE TABLE lesson_progress (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  enrollment_id VARCHAR(64) NOT NULL,
  lesson_id VARCHAR(64) NOT NULL,
  status ENUM('not_started', 'in_progress', 'completed') DEFAULT 'not_started',
  progress_percentage DECIMAL(5,2) DEFAULT 0.00,
  time_spent_minutes INT DEFAULT 0,
  started_at DATETIME,
  completed_at DATETIME,
  last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  quiz_score DECIMAL(5,2),
  assignment_status ENUM('not_submitted', 'submitted', 'graded') DEFAULT 'not_submitted',
  assignment_score DECIMAL(5,2),
  UNIQUE KEY uniq_enrollment_lesson (enrollment_id, lesson_id),
  FOREIGN KEY (enrollment_id) REFERENCES course_enrollments(id),
  FOREIGN KEY (lesson_id) REFERENCES course_lessons(id),
  INDEX idx_enrollment (enrollment_id),
  idx_lesson (lesson_id),
  idx_status (status),
  idx_completed (completed_at)
) ENGINE=InnoDB;

CREATE TABLE certifications (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(256) NOT NULL,
  description TEXT,
  certification_type ENUM('course_completion', 'skill_assessment', 'professional') DEFAULT 'course_completion',
  requirements JSON, -- Required courses, skills, experience
  validity_months INT, -- Certificate validity period
  status ENUM('active', 'inactive') DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type (certification_type),
  idx_status (status)
) ENGINE=InnoDB;

CREATE TABLE user_certifications (
  id VARCHAR(64) PRIMARY KEY,
  user_id BIGINT NOT NULL,
  certification_id VARCHAR(64) NOT NULL,
  status ENUM('in_progress', 'awarded', 'expired', 'revoked') DEFAULT 'in_progress',
  awarded_at DATETIME,
  expires_at DATETIME,
  certificate_url VARCHAR(512),
  verification_code VARCHAR(128) UNIQUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (certification_id) REFERENCES certifications(id),
  INDEX idx_user (user_id),
  idx_certification (certification_id),
  idx_status (status),
  idx_awarded (awarded_at),
  idx_expires (expires_at)
) ENGINE=InnoDB;

CREATE TABLE faqs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  question VARCHAR(512) NOT NULL,
  answer LONGTEXT NOT NULL,
  category_id BIGINT,
  priority INT DEFAULT 0,
  language VARCHAR(10) DEFAULT 'en',
  view_count INT DEFAULT 0,
  helpful_count INT DEFAULT 0,
  not_helpful_count INT DEFAULT 0,
  status ENUM('active', 'hidden') DEFAULT 'active',
  created_by BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES article_categories(id),
  INDEX idx_category (category_id),
  idx_priority (priority),
  idx_language (language),
  idx_status (status),
  FULLTEXT idx_search (question, answer)
) ENGINE=InnoDB;

CREATE TABLE release_notes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  version VARCHAR(64) NOT NULL,
  title VARCHAR(512) NOT NULL,
  content LONGTEXT NOT NULL,
  release_type ENUM('major', 'minor', 'patch', 'hotfix') DEFAULT 'minor',
  release_date DATE NOT NULL,
  status ENUM('draft', 'published') DEFAULT 'draft',
  published_by BIGINT,
  published_at DATETIME,
  view_count INT DEFAULT 0,
  breaking_changes JSON,
  new_features JSON,
  bug_fixes JSON,
  security_updates JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_version (version),
  idx_type (release_type),
  idx_date (release_date),
  idx_status (status),
  idx_published (published_at)
) ENGINE=InnoDB;

CREATE TABLE glossary_terms (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  term VARCHAR(256) NOT NULL UNIQUE,
  definition TEXT NOT NULL,
  category VARCHAR(128),
  abbreviation VARCHAR(64),
  related_terms JSON, -- Array of related term IDs
  synonyms JSON, -- Array of synonyms
  language VARCHAR(10) DEFAULT 'en',
  status ENUM('active', 'hidden') DEFAULT 'active',
  created_by BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_term (term),
  idx_category (category),
  idx_language (language),
  idx_status (status),
  FULLTEXT idx_search (term, definition)
) ENGINE=InnoDB;

CREATE TABLE knowledge_search_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT,
  query VARCHAR(512) NOT NULL,
  filters JSON, -- Search filters applied
  results_count INT,
  clicked_article_id VARCHAR(64),
  session_id VARCHAR(128),
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user (user_id),
  idx_query (query),
  idx_session (session_id),
  idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE user_bookmarks (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  article_id VARCHAR(64),
  tutorial_id VARCHAR(64),
  course_id VARCHAR(64),
  bookmark_type ENUM('article', 'tutorial', 'course') NOT NULL,
  folder VARCHAR(128), -- Bookmark folder/category
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (article_id) REFERENCES knowledge_articles(id),
  FOREIGN KEY (tutorial_id) REFERENCES tutorials(id),
  FOREIGN KEY (course_id) REFERENCES courses(id),
  INDEX idx_user (user_id),
  idx_type (bookmark_type),
  idx_folder (folder),
  idx_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE user_reading_progress (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  article_id VARCHAR(64),
  tutorial_id VARCHAR(64),
  content_type ENUM('article', 'tutorial') NOT NULL,
  progress_percentage DECIMAL(5,2) DEFAULT 0.00,
  current_position INT DEFAULT 0, -- Character or scroll position
    time_spent_minutes INT DEFAULT 0,
  last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  completed_at DATETIME,
  UNIQUE KEY uniq_user_content (user_id, COALESCE(article_id, ''), COALESCE(tutorial_id, ''), content_type),
  FOREIGN KEY (article_id) REFERENCES knowledge_articles(id),
  FOREIGN KEY (tutorial_id) REFERENCES tutorials(id),
  INDEX idx_user (user_id),
  idx_content_type (content_type),
  idx_progress (progress_percentage),
  idx_last_accessed (last_accessed_at)
) ENGINE=InnoDB;
```

### 4.2 ER Diagram (Textual)

```
knowledge_articles (1) → (n) article_versions
knowledge_articles (1) → (n) article_comments
knowledge_articles (1) → (n) article_ratings
knowledge_articles (n) → (n) article_tags (through article_tag_relations)
knowledge_articles (1) → (n) user_reading_progress

article_categories (1) → (n) knowledge_articles
article_categories (1) → (n) tutorials
article_categories (1) → (n) courses
article_categories (1) → (n) faqs

courses (1) → (n) course_modules
course_modules (1) → (n) course_lessons
courses (1) → (n) course_enrollments

course_enrollments (1) → (n) lesson_progress

certifications (1) → (n) user_certifications

users (1) → (n) knowledge_articles (as author)
users (1) → (n) tutorials (as author)
users (1) → (n) course_enrollments
users (1) → (n) user_certifications
users (1) → (n) user_bookmarks
users (1) → (n) user_reading_progress
users (1) → (n) knowledge_search_logs
```

---

## 5. API Specification

### 5.1 Documentation and Knowledge API Endpoints

Base path: `/api/v1/knowledge`

| Method | Path | Description |
|--------|------|-------------|
| **Articles** | | |
| GET | `/articles` | List articles with filtering and pagination. |
| GET | `/articles/{id}` | Get article details. |
| POST | `/articles` | Create new article. |
| PUT | `/articles/{id}` | Update article. |
| DELETE | `/articles/{id}` | Delete article. |
| POST | `/articles/{id}/publish` | Publish article. |
| GET | `/articles/{id}/versions` | Get article version history. |
| **Search** | | |
| GET | `/search` | Search knowledge base. |
| GET | `/search/suggestions` | Get search suggestions. |
| POST | `/search/feedback` | Provide search feedback. |
| **Categories** | | |
| GET | `/categories` | List categories. |
| GET | `/categories/{id}` | Get category details. |
| POST | `/categories` | Create category. |
| **Tutorials** | | |
| GET | `/tutorials` | List tutorials. |
| GET | `/tutorials/{id}` | Get tutorial details. |
| POST | `/tutorials/{id}/start` | Start tutorial session. |
| POST | `/tutorials/sessions/{id}/step` | Execute tutorial step. |
| **Courses** | | |
| GET | `/courses` | List courses. |
| GET | `/courses/{id}` | Get course details. |
| POST | `/courses/{id}/enroll` | Enroll in course. |
| GET | `/courses/{id}/progress` | Get course progress. |
| **Learning** | | |
| GET | `/learning/paths` | Get learning paths. |
| GET | `/learning/progress` | Get overall learning progress. |
| POST | `/learning/complete` | Mark content as completed. |
| **User** | | |
| GET | `/user/bookmarks` | Get user bookmarks. |
| POST | `/user/bookmarks` | Add bookmark. |
| DELETE | `/user/bookmarks/{id}` | Remove bookmark. |
| GET | `/user/progress` | Get user reading progress. |
| POST | `/user/progress` | Update reading progress. |

### 5.2 Example: Search Knowledge Base

```http
GET /api/v1/knowledge/search?q=ETL%20pipeline&type=article&category=data-engineering&language=en&page=1&limit=20
```

Response:
```json
{
  "query": "ETL pipeline",
  "results": [
    {
      "id": "article_123",
      "title": "ETL Pipeline Configuration Guide",
      "type": "article",
      "category": "Data Engineering",
      "summary": "Comprehensive guide for configuring ETL pipelines in AEDIP...",
      "url": "/knowledge/articles/etl-pipeline-configuration",
      "relevance_score": 0.95,
      "last_updated": "2026-07-14T14:30:00Z",
      "reading_time": 15,
      "difficulty": "intermediate"
    }
  ],
  "total_results": 45,
  "page": 1,
  "limit": 20,
  "facets": {
    "categories": [
      {"name": "Data Engineering", "count": 23},
      {"name": "User Guides", "count": 12}
    ],
    "types": [
      {"name": "article", "count": 30},
      {"name": "tutorial", "count": 15}
    ]
  },
  "suggestions": [
    "ETL data validation",
    "Pipeline monitoring",
    "Data transformation"
  ]
}
```

---

## 6. Backend Architecture

### 6.1 Documentation Service Architecture

```python
class DocumentationService:
    """Main documentation service for AEDIP."""
    
    def __init__(self, 
                 config: DocumentationConfig,
                 content_manager: ContentManager,
                 search_engine: SearchEngine,
                 ai_services: AIServices):
        self.config = config
        self.content = content_manager
        self.search = search_engine
        self.ai = ai_services
        self.cache = RedisCache()
    
    async def initialize(self):
        """Initialize documentation service."""
        
        # Initialize content manager
        await self.content.initialize()
        
        # Setup search engine with indexing
        await self.search.initialize()
        
        # Initialize AI services
        await self.ai.initialize()
        
        # Setup content synchronization
        await self.setup_content_sync()
        
        # Start background tasks
        asyncio.create_task(self.content_indexer())
        asyncio.create_task(self.analytics_processor())
        
        logger.info("Documentation service initialized")
    
    async def get_article(self, 
                         article_id: str,
                         user_context: UserContext) -> ArticleResponse:
        """Get article with personalization."""
        
        # Check cache first
        cache_key = f"article:{article_id}:{user_context.user_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Get article from database
        article = await self.content.get_article(article_id, user_context)
        
        # Generate AI summary
        summary = await self.ai.generate_summary(article.content)
        
        # Get related articles
        related = await self.get_related_articles(article, user_context)
        
        # Get user progress
        progress = await self.get_user_progress(
            user_context.user_id, 
            article_id
        )
        
        # Check user permissions
        await self.check_read_permissions(article, user_context)
        
        # Create response
        response = ArticleResponse(
            article=article,
            summary=summary,
            related_articles=related,
            user_progress=progress,
            personalized_recommendations=await self.get_recommendations(
                article, user_context
            )
        )
        
        # Cache response
        await self.cache.set(cache_key, response, ttl=300)  # 5 minutes
        
        return response
    
    async def search_content(self, 
                           query: SearchQuery,
                           user_context: UserContext) -> SearchResult:
        """Search content with AI enhancement."""
        
        # Log search
        await self.log_search(user_context.user_id, query)
        
        # Perform search
        search_result = await self.search.search(
            query=query,
            user_context=user_context,
            filters=query.filters
        )
        
        # Enhance with AI
        if query.ai_enhanced:
            # Generate query expansion
            expanded_query = await self.ai.expand_query(query.text)
            
            # Get AI-ranked results
            ai_ranked = await self.ai.rank_results(
                query=expanded_query,
                results=search_result.results,
                user_context=user_context
            )
            search_result.results = ai_ranked
            
            # Generate suggestions
            search_result.suggestions = await self.ai.generate_suggestions(
                query=query.text,
                results=search_result.results
            )
        
        return search_result
    
    async def content_indexer(self):
        """Background task to index content for search."""
        
        while True:
            try:
                # Get unindexed content
                unindexed = await self.content.get_unindexed_content()
                
                for content in unindexed:
                    # Index content
                    await self.search.index_content(content)
                    
                    # Mark as indexed
                    await self.content.mark_as_indexed(content.id)
                
                # Wait before next batch
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Content indexing error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

class AIContentGenerator:
    """AI-powered content generation and enhancement."""
    
    def __init__(self, ai_service: AIService):
        self.ai = ai_service
    
    async def generate_article_from_code(self, 
                                       code_context: CodeContext) -> ArticleDraft:
        """Generate documentation from code."""
        
        # Analyze code structure
        code_analysis = await self.analyze_code_structure(code_context)
        
        # Extract documentation requirements
        doc_requirements = await self.extract_doc_requirements(code_analysis)
        
        # Generate article outline
        outline = await self.generate_article_outline(doc_requirements)
        
        # Generate content for each section
        sections = []
        for section in outline.sections:
            content = await self.generate_section_content(
                section=section,
                code_context=code_context,
                analysis=code_analysis
            )
            sections.append(content)
        
        # Generate examples
        examples = await self.generate_code_examples(
            code_context=code_context,
            sections=outline.sections
        )
        
        return ArticleDraft(
            title=outline.title,
            sections=sections,
            examples=examples,
            metadata={
                'generated_from': code_context.file_path,
                'generated_at': datetime.utcnow(),
                'confidence_score': outline.confidence_score
            }
        )
    
    async def generate_api_documentation(self, 
                                       openapi_spec: dict) -> APIDocumentation:
        """Generate comprehensive API documentation."""
        
        # Parse OpenAPI spec
        parsed_spec = await self.parse_openapi_spec(openapi_spec)
        
        # Generate overview
        overview = await self.generate_api_overview(parsed_spec)
        
        # Generate endpoint documentation
        endpoints = []
        for endpoint in parsed_spec.endpoints:
            doc = await self.generate_endpoint_doc(endpoint)
            endpoints.append(doc)
        
        # Generate authentication guide
        auth_guide = await self.generate_auth_guide(parsed_spec)
        
        # Generate SDK examples
        sdk_examples = await self.generate_sdk_examples(parsed_spec)
        
        return APIDocumentation(
            overview=overview,
            endpoints=endpoints,
            authentication=auth_guide,
            sdk_examples=sdk_examples,
            openapi_spec=openapi_spec
        )
    
    async def summarize_article(self, content: str) -> ArticleSummary:
        """Generate AI-powered article summary."""
        
        # Extract key points
        key_points = await self.ai.extract_key_points(content)
        
        # Generate executive summary
        executive_summary = await self.ai.generate_executive_summary(content)
        
        # Generate bullet points
        bullet_points = await self.ai.generate_bullet_points(content)
        
        # Generate tl;dr
        tldr = await self.ai.generate_tldr(content)
        
        return ArticleSummary(
            executive_summary=executive_summary,
            key_points=key_points,
            bullet_points=bullet_points,
            tldr=tldr,
            estimated_reading_time=self.calculate_reading_time(content)
        )
    
    async def translate_article(self, 
                              content: str,
                              target_language: str) -> TranslationResult:
        """Translate article to target language."""
        
        # Detect source language
        source_language = await self.ai.detect_language(content)
        
        # Translate content
        translated_content = await self.ai.translate_text(
            text=content,
            source_language=source_language,
            target_language=target_language
        )
        
        # Preserve code blocks and technical terms
        preserved_content = await self.preserve_technical_elements(
            original_content=content,
            translated_content=translated_content
        )
        
        # Validate translation quality
        quality_score = await self.ai.validate_translation_quality(
            original=content,
            translated=preserved_content,
            languages=[source_language, target_language]
        )
        
        return TranslationResult(
            original_language=source_language,
            target_language=target_language,
            translated_content=preserved_content,
            quality_score=quality_score,
            confidence=quality_score.confidence
        )
```

---

## 7. Frontend Architecture

### 7.1 Documentation Portal Frontend

```typescript
// Main Documentation Portal Component
const DocumentationPortal: React.FC = () => {
  const [currentView, setCurrentView] = useState<'knowledge' | 'learning' | 'admin'>('knowledge');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [userProgress, setUserProgress] = useState<UserProgress | null>(null);
  
  useEffect(() => {
    loadUserProgress();
    setupKeyboardShortcuts();
  }, []);
  
  const loadUserProgress = async () => {
    const progress = await getUserProgress();
    setUserProgress(progress);
  };
  
  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    
    if (query.trim()) {
      const results = await searchContent({
        q: query,
        ai_enhanced: true,
        include_suggestions: true
      });
      setSearchResults(results);
    } else {
      setSearchResults(null);
    }
  };
  
  return (
    <div className="documentation-portal">
      <Header 
        currentView={currentView}
        onViewChange={setCurrentView}
        onSearch={handleSearch}
        userProgress={userProgress}
      />
      
      <div className="portal-content">
        <Sidebar 
          currentView={currentView}
          userProgress={userProgress}
        />
        
        <main className="main-content">
          {searchResults ? (
            <SearchResults 
              results={searchResults}
              query={searchQuery}
              onClose={() => setSearchResults(null)}
            />
          ) : (
            <>
              {currentView === 'knowledge' && <KnowledgePortal />}
              {currentView === 'learning' && <LearningCenter />}
              {currentView === 'admin' && <AdminPanel />}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

// Article Viewer Component
const ArticleViewer: React.FC<{
  article: Article;
  onProgressUpdate?: (progress: number) => void;
}> = ({ article, onProgressUpdate }) => {
  const [content, setContent] = useState<string>('');
  const [summary, setSummary] = useState<ArticleSummary | null>(null);
  const [relatedArticles, setRelatedArticles] = useState<Article[]>([]);
  const [userNotes, setUserNotes] = useState<string>('');
  const [bookmarked, setBookmarked] = useState(false);
  const [readingProgress, setReadingProgress] = useState(0);
  
  useEffect(() => {
    loadArticleContent();
    loadArticleSummary();
    loadRelatedArticles();
    checkBookmarkStatus();
  }, [article.id]);
  
  const loadArticleContent = async () => {
    const content = await getArticleContent(article.id);
    setContent(content);
    
    // Setup reading progress tracking
    setupReadingProgressTracking(content);
  };
  
  const setupReadingProgressTracking = (content: string) => {
    const articleElement = document.getElementById('article-content');
    if (!articleElement) return;
    
    const handleScroll = () => {
      const scrollTop = articleElement.scrollTop;
      const scrollHeight = articleElement.scrollHeight - articleElement.clientHeight;
      const progress = (scrollTop / scrollHeight) * 100;
      
      setReadingProgress(progress);
      onProgressUpdate?.(progress);
      
      // Save progress to backend
      debouncedSaveProgress(progress);
    };
    
    articleElement.addEventListener('scroll', handleScroll);
    
    return () => {
      articleElement.removeEventListener('scroll', handleScroll);
    };
  };
  
  const debouncedSaveProgress = debounce(async (progress: number) => {
    await updateReadingProgress(article.id, progress);
  }, 5000);
  
  const handleBookmark = async () => {
    if (bookmarked) {
      await removeBookmark(article.id);
      setBookmarked(false);
    } else {
      await addBookmark(article.id, { notes: userNotes });
      setBookmarked(true);
    }
  };
  
  const handleAddNote = async (note: string) => {
    await addArticleNote(article.id, note);
    setUserNotes(note);
  };
  
  return (
    <div className="article-viewer">
      <div className="article-header">
        <div className="article-meta">
          <span className="category">{article.category}</span>
          <span className="difficulty">{article.difficulty}</span>
          <span className="reading-time">{article.readingTime} min read</span>
        </div>
        
        <div className="article-actions">
          <button 
            className={`bookmark-btn ${bookmarked ? 'bookmarked' : ''}`}
            onClick={handleBookmark}
          >
            <BookmarkIcon />
            {bookmarked ? 'Bookmarked' : 'Bookmark'}
          </button>
          
          <button className="share-btn" onClick={() => shareArticle(article)}>
            <ShareIcon />
            Share
          </button>
          
          <button className="print-btn" onClick={() => printArticle(article)}>
            <PrintIcon />
            Print
          </button>
        </div>
      </div>
      
      <h1 className="article-title">{article.title}</h1>
      
      {summary && (
        <div className="article-summary">
          <details>
            <summary>AI Summary</summary>
            <div className="summary-content">
              <p>{summary.executiveSummary}</p>
              <ul>
                {summary.keyPoints.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>
          </details>
        </div>
      )}
      
      <div 
        id="article-content"
        className="article-content"
        dangerouslySetInnerHTML={{ __html: content }}
      />
      
      <div className="article-footer">
        <div className="reading-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${readingProgress}%` }}
            />
          </div>
          <span>{Math.round(readingProgress)}% complete</span>
        </div>
        
        <div className="user-notes">
          <h3>Your Notes</h3>
          <textarea
            value={userNotes}
            onChange={(e) => setUserNotes(e.target.value)}
            onBlur={() => handleAddNote(userNotes)}
            placeholder="Add your notes here..."
          />
        </div>
        
        {relatedArticles.length > 0 && (
          <div className="related-articles">
            <h3>Related Articles</h3>
            <div className="related-grid">
              {relatedArticles.map((related) => (
                <ArticleCard 
                  key={related.id}
                  article={related}
                  compact
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Interactive Tutorial Component
const InteractiveTutorial: React.FC<{
  tutorial: Tutorial;
}> = ({ tutorial }) => {
  const [session, setSession] = useState<TutorialSession | null>(null);
  const [currentStep, setCurrentStep] = useState<TutorialStep | null>(null);
  const [stepInput, setStepInput] = useState<StepInput | null>(null);
  const [stepResult, setStepResult] = useState<StepResult | null>(null);
  const [labEnvironment, setLabEnvironment] = useState<LabEnvironment | null>(null);
  
  useEffect(() => {
    startTutorial();
  }, [tutorial.id]);
  
  const startTutorial = async () => {
    const session = await startTutorialSession(tutorial.id);
    setSession(session);
    
    if (tutorial.requiresLab) {
      const labEnv = await createLabEnvironment(session.id);
      setLabEnvironment(labEnv);
    }
    
    setCurrentStep(tutorial.steps[0]);
  };
  
  const executeStep = async (input: StepInput) => {
    if (!session || !currentStep) return;
    
    setStepInput(input);
    
    const result = await executeTutorialStep(session.id, input);
    setStepResult(result);
    
    if (result.completed && session.currentStep < tutorial.steps.length - 1) {
      const nextStep = tutorial.steps[session.currentStep + 1];
      setCurrentStep(nextStep);
    }
  };
  
  return (
    <div className="interactive-tutorial">
      <div className="tutorial-header">
        <h2>{tutorial.title}</h2>
        <div className="tutorial-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ 
                width: `${((session?.currentStep || 0) + 1) / tutorial.steps.length * 100}%` 
              }}
            />
          </div>
          <span>
            Step {session?.currentStep + 1 || 0} of {tutorial.steps.length}
          </span>
        </div>
      </div>
      
      <div className="tutorial-content">
        <div className="step-instructions">
          {currentStep && (
            <div className="step-content">
              <h3>{currentStep.title}</h3>
              <div dangerouslySetInnerHTML={{ __html: currentStep.content }} />
              
              {currentStep.type === 'interactive' && labEnvironment && (
                <InteractiveStep
                  step={currentStep}
                  environment={labEnvironment}
                  onExecute={executeStep}
                  result={stepResult}
                />
              )}
              
              {currentStep.type === 'quiz' && (
                <QuizStep
                  step={currentStep}
                  onAnswer={executeStep}
                  result={stepResult}
                />
              )}
            </div>
          )}
        </div>
        
        {labEnvironment && (
          <div className="lab-environment">
            <LabTerminal
              environment={labEnvironment}
              onCommand={(command) => executeStep({ action: 'command', code: command })}
            />
          </div>
        )}
      </div>
      
      {stepResult && (
        <div className={`step-result ${stepResult.success ? 'success' : 'error'}`}>
          <h4>Result</h4>
          <pre>{JSON.stringify(stepResult.execution_result, null, 2)}</pre>
          {stepResult.feedback && (
            <div className="ai-feedback">
              <h5>AI Feedback</h5>
              <p>{stepResult.feedback}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

---

## 8. AI Documentation Integration

### 8.1 AI-Powered Documentation Services

```python
class AIDocumentationServices:
    """AI-powered documentation services."""
    
    def __init__(self, 
                 llm_service: LLMService,
                 embedding_service: EmbeddingService,
                 translation_service: TranslationService):
        self.llm = llm_service
        self.embeddings = embedding_service
        self.translation = translation_service
    
    async def generate_documentation_from_api(self, 
                                            api_spec: dict) -> GeneratedDocumentation:
        """Generate documentation from API specification."""
        
        # Analyze API structure
        api_analysis = await self.analyze_api_structure(api_spec)
        
        # Generate comprehensive documentation
        documentation = GeneratedDocumentation()
        
        # Generate overview
        documentation.overview = await self.generate_api_overview(api_analysis)
        
        # Generate authentication guide
        documentation.authentication = await self.generate_auth_guide(api_analysis)
        
        # Generate endpoint documentation
        for endpoint in api_analysis.endpoints:
            endpoint_doc = await self.generate_endpoint_documentation(endpoint)
            documentation.endpoints.append(endpoint_doc)
        
        # Generate SDK examples
        documentation.sdk_examples = await self.generate_sdk_examples(api_analysis)
        
        # Generate tutorials
        documentation.tutorials = await self.generate_api_tutorials(api_analysis)
        
        return documentation
    
    async def generate_smart_search(self, 
                                  query: str,
                                  user_context: UserContext) -> SmartSearchResult:
        """Generate AI-enhanced search results."""
        
        # Expand query with semantic understanding
        expanded_query = await self.expand_query_semantically(query)
        
        # Get user's knowledge graph
        user_knowledge = await self.get_user_knowledge_graph(user_context.user_id)
        
        # Search with context awareness
        search_results = await self.contextual_search(
            query=expanded_query,
            user_knowledge=user_knowledge,
            user_context=user_context
        )
        
        # Rank results with AI
        ranked_results = await self.ai_rank_results(
            query=query,
            results=search_results,
            user_context=user_context
        )
        
        # Generate explanations
        explanations = await self.generate_result_explanations(
            query=query,
            results=ranked_results,
            user_context=user_context
        )
        
        # Suggest follow-up queries
        follow_up_queries = await self.suggest_follow_up_queries(
            query=query,
            results=ranked_results,
            user_context=user_context
        )
        
        return SmartSearchResult(
            query=query,
            expanded_query=expanded_query,
            results=ranked_results,
            explanations=explanations,
            follow_up_queries=follow_up_queries,
            confidence_score=self.calculate_search_confidence(ranked_results)
        )
    
    async def generate_personalized_learning_path(self, 
                                                user_id: str,
                                                learning_goal: str) -> LearningPath:
        """Generate personalized learning path."""
        
        # Assess user's current knowledge
        current_knowledge = await self.assess_user_knowledge(user_id)
        
        # Analyze learning goal
        goal_analysis = await self.analyze_learning_goal(learning_goal)
        
        # Identify knowledge gaps
        knowledge_gaps = self.identify_knowledge_gaps(
            current_knowledge,
            goal_analysis
        )
        
        # Get available learning resources
        available_resources = await self.get_learning_resources(knowledge_gaps)
        
        # Generate optimal learning path
        learning_path = await self.generate_optimal_path(
            user_knowledge=current_knowledge,
            knowledge_gaps=knowledge_gaps,
            resources=available_resources,
            learning_style=await self.get_user_learning_style(user_id)
        )
        
        # Personalize content recommendations
        for module in learning_path.modules:
            module.personalized_content = await self.personalize_content(
                content=module.content,
                user_context=await self.get_user_context(user_id)
            )
        
        return learning_path
    
    async def generate_article_summary(self, 
                                     content: str,
                                     summary_type: str = 'comprehensive') -> ArticleSummary:
        """Generate AI-powered article summary."""
        
        if summary_type == 'comprehensive':
            # Generate detailed summary
            summary = await self.llm.generate_response(
                prompt=f"""
                Generate a comprehensive summary of the following article:
                
                {content}
                
                Include:
                1. Executive summary (2-3 sentences)
                2. Key points (bullet points)
                3. Main concepts explained
                4. Practical takeaways
                5. Related topics to explore
                """,
                max_tokens=500
            )
        elif summary_type == 'brief':
            # Generate brief summary
            summary = await self.llm.generate_response(
                prompt=f"""
                Generate a brief summary (tl;dr) of the following article in 1-2 sentences:
                
                {content}
                """,
                max_tokens=100
            )
        elif summary_type == 'key_points':
            # Generate key points only
            summary = await self.llm.generate_response(
                prompt=f"""
                Extract the key points from the following article as bullet points:
                
                {content}
                """,
                max_tokens=300
            )
        
        # Parse and structure summary
        parsed_summary = self.parse_summary_response(summary)
        
        return ArticleSummary(
            type=summary_type,
            executive_summary=parsed_summary.get('executive_summary', ''),
            key_points=parsed_summary.get('key_points', []),
            main_concepts=parsed_summary.get('main_concepts', []),
            practical_takeaways=parsed_summary.get('practical_takeaways', []),
            related_topics=parsed_summary.get('related_topics', []),
            confidence_score=0.85  # Default confidence
        )
    
    async def translate_and_localize(self, 
                                   content: string,
                                   target_language: str,
                                   preserve_technical: bool = True) -> LocalizationResult:
        """Translate and localize content."""
        
        # Detect source language
        source_language = await self.translation.detect_language(content)
        
        # Extract technical terms to preserve
        technical_terms = []
        if preserve_technical:
            technical_terms = await self.extract_technical_terms(content)
        
        # Translate content
        translated_content = await self.translation.translate(
            text=content,
            source_language=source_language,
            target_language=target_language,
            preserve_terms=technical_terms
        )
        
        # Localize cultural references
        localized_content = await self.localize_cultural_references(
            content=translated_content,
            target_language=target_language
        )
        
        # Adapt examples for target audience
        adapted_content = await self.adapt_examples(
            content=localized_content,
            target_language=target_language
        )
        
        # Validate translation quality
        quality_score = await self.validate_translation_quality(
            original=content,
            translated=adapted_content,
            source_language=source_language,
            target_language=target_language
        )
        
        return LocalizationResult(
            source_language=source_language,
            target_language=target_language,
            translated_content=adapted_content,
            preserved_terms=technical_terms,
            quality_score=quality_score,
            confidence=quality_score.confidence
        )
```

---

## 9. Search Strategy

### 9.1 Advanced Search Implementation

```python
class AdvancedSearchEngine:
    """Advanced search engine with AI capabilities."""
    
    def __init__(self, 
                 index_manager: IndexManager,
                 query_processor: QueryProcessor,
                 ranking_engine: RankingEngine):
        self.index = index_manager
        self.processor = query_processor
        self.ranking = ranking_engine
    
    async def search(self, 
                    query: SearchQuery,
                    user_context: UserContext) -> SearchResult:
        """Execute advanced search with AI enhancement."""
        
        # Process query
        processed_query = await self.processor.process_query(query)
        
        # Search multiple indices
        search_results = await self.search_multiple_indices(
            processed_query,
            user_context
        )
        
        # Apply AI ranking
        ranked_results = await self.ranking.rank_results(
            results=search_results,
            query=processed_query,
            user_context=user_context
        )
        
        # Generate explanations
        explanations = await self.generate_explanations(
            query=processed_query,
            results=ranked_results,
            user_context=user_context
        )
        
        # Generate suggestions
        suggestions = await self.generate_suggestions(
            query=processed_query,
            results=ranked_results,
            user_context=user_context
        )
        
        return SearchResult(
            query=query.text,
            results=ranked_results,
            total_count=len(ranked_results),
            explanations=explanations,
            suggestions=suggestions,
            facets=await self.calculate_facets(ranked_results),
            search_time=processed_query.processing_time
        )
    
    async def search_multiple_indices(self, 
                                    query: ProcessedQuery,
                                    user_context: UserContext) -> List[SearchResult]:
        """Search across multiple content indices."""
        
        results = []
        
        # Search articles
        article_results = await self.index.search_articles(
            query=query,
            filters=user_context.filters
        )
        results.extend(article_results)
        
        # Search tutorials
        tutorial_results = await self.index.search_tutorials(
            query=query,
            filters=user_context.filters
        )
        results.extend(tutorial_results)
        
        # Search API documentation
        api_results = await self.index.search_api_docs(
            query=query,
            filters=user_context.filters
        )
        results.extend(api_results)
        
        # Search code examples
        code_results = await self.index.search_code_examples(
            query=query,
            filters=user_context.filters
        )
        results.extend(code_results)
        
        return results
    
    async def generate_explanations(self, 
                                  query: ProcessedQuery,
                                  results: List[SearchResult],
                                  user_context: UserContext) -> List[SearchExplanation]:
        """Generate AI-powered explanations for search results."""
        
        explanations = []
        
        for result in results[:5]:  # Explain top 5 results
            explanation = await self.ai.generate_explanation(
                query=query.original,
                result=result,
                user_context=user_context
            )
            explanations.append(explanation)
        
        return explanations
    
    async def generate_suggestions(self, 
                                 query: ProcessedQuery,
                                 results: List[SearchResult],
                                 user_context: UserContext) -> List<SearchSuggestion]:
        """Generate intelligent search suggestions."""
        
        suggestions = []
        
        # Query refinement suggestions
        refinements = await self.generate_query_refinements(
            query=query,
            results=results
        )
        suggestions.extend(refinements)
        
        # Related topic suggestions
        related_topics = await self.generate_related_topics(
            query=query,
            results=results,
            user_context=user_context
        )
        suggestions.extend(related_topics)
        
        # User-specific suggestions
        user_suggestions = await self.generate_user_suggestions(
            query=query,
            user_context=user_context
        )
        suggestions.extend(user_suggestions)
        
        return suggestions[:10]  # Return top 10 suggestions

class SemanticSearch:
    """Semantic search using embeddings."""
    
    def __init__(self, 
                 embedding_service: EmbeddingService,
                 vector_store: VectorStore):
        self.embeddings = embedding_service
        self.vector_store = vector_store
    
    async def semantic_search(self, 
                            query: str,
                            content_type: str = None,
                            limit: int = 10) -> List[SemanticSearchResult]:
        """Perform semantic search using embeddings."""
        
        # Generate query embedding
        query_embedding = await self.embeddings.generate_embedding(query)
        
        # Search vector store
        similar_vectors = await self.vector_store.search_similar(
            query_vector=query_embedding,
            content_type=content_type,
            limit=limit
        )
        
        # Calculate semantic similarity scores
        results = []
        for vector in similar_vectors:
            similarity_score = self.calculate_cosine_similarity(
                query_embedding,
                vector.embedding
            )
            
            results.append(SemanticSearchResult(
                content_id=vector.content_id,
                content_type=vector.content_type,
                title=vector.title,
                snippet=vector.snippet,
                similarity_score=similarity_score,
                url=vector.url
            ))
        
        # Sort by similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results
    
    async def find_similar_content(self, 
                                 content_id: str,
                                 limit: int = 5) -> List[SimilarContentResult]:
        """Find content similar to given content."""
        
        # Get content embedding
        content_embedding = await self.vector_store.get_embedding(content_id)
        
        # Search for similar content
        similar_vectors = await self.vector_store.search_similar(
            query_vector=content_embedding,
            exclude_content_id=content_id,
            limit=limit
        )
        
        # Process results
        results = []
        for vector in similar_vectors:
            similarity_score = self.calculate_cosine_similarity(
                content_embedding,
                vector.embedding
            )
            
            results.append(SimilarContentResult(
                content_id=vector.content_id,
                title=vector.title,
                similarity_score=similarity_score,
                similarity_reason=self.explain_similarity(content_id, vector.content_id)
            ))
        
        return results
```

---

## 10. Administrator Guide

### 10.1 Documentation Management

- **Content Management**: Create, edit, and manage documentation content.
- **Workflow Management**: Configure approval workflows and content review processes.
- **User Management**: Manage user access and permissions for documentation.
- **Analytics**: Monitor documentation usage, search patterns, and user engagement.
- **Content Governance**: Ensure content quality, consistency, and compliance.

### 10.2 System Configuration

- **Search Configuration**: Configure search engines, indexing, and ranking algorithms.
- **AI Services**: Configure AI services for content generation and enhancement.
- **Multilingual Support**: Setup translation and localization features.
- **Integration**: Configure integrations with external systems and APIs.

---

## 11. Developer Guide

### 11.1 API Documentation

- **OpenAPI Specification**: Automatic generation of API documentation from code.
- **Interactive Documentation**: Live API testing and exploration.
- **SDK Documentation**: Comprehensive SDK guides and examples.
- **Code Examples**: Curated code examples for different use cases.

### 11.2 Content Development

- **Markdown Format**: Use standardized markdown format for documentation.
- **Code Integration**: Automatic documentation generation from code comments.
- **Version Control**: Documentation versioning and change tracking.
- **Content Templates**: Use templates for consistent documentation structure.

---

## 12. User Guide

### 12.1 Knowledge Portal Usage

- **Searching Content**: Use advanced search with filters and AI suggestions.
- **Browsing Content**: Navigate categories and topics intuitively.
- **Personalization**: Customize content recommendations and bookmarks.
- **Offline Access**: Download content for offline reading.

### 12.2 Learning Center

- **Course Enrollment**: Enroll in courses and track progress.
- **Interactive Tutorials**: Complete hands-on tutorials with live environments.
- **Certification**: Earn certifications and badges.
- **Learning Paths**: Follow personalized learning paths.

---

## 13. Content Governance Strategy

### 13.1 Content Lifecycle

```python
class ContentGovernance:
    """Content governance and lifecycle management."""
    
    def __init__(self, 
                 workflow_engine: WorkflowEngine,
                 quality_checker: QualityChecker,
                 compliance_monitor: ComplianceMonitor):
        self.workflow = workflow_engine
        self.quality = quality_checker
        self.compliance = compliance_monitor
    
    async def manage_content_lifecycle(self, 
                                     content: Content,
                                     event: LifecycleEvent) -> LifecycleResult:
        """Manage content through its lifecycle."""
        
        # Validate event
        validation = await self.validate_lifecycle_event(content, event)
        if not validation.is_valid:
            raise LifecycleError(validation.errors)
        
        # Execute workflow step
        workflow_result = await self.workflow.execute_step(
            content_id=content.id,
            event=event,
            context=content.context
        )
        
        # Update content status
        content.status = workflow_result.new_status
        content.updated_at = datetime.utcnow()
        
        # Run quality checks
        if event.requires_quality_check:
            quality_result = await self.quality.check_content(content)
            if not quality_result.passed:
                content.status = 'review_required'
                await self.notify_quality_issues(content, quality_result)
        
        # Compliance check
        if event.requires_compliance_check:
            compliance_result = await self.compliance.check_compliance(content)
            if not compliance_result.compliant:
                await self.handle_compliance_issues(content, compliance_result)
        
        return LifecycleResult(
            content=content,
            workflow_result=workflow_result,
            quality_result=quality_result if event.requires_quality_check else None,
            compliance_result=compliance_result if event.requires_compliance_check else None
        )
    
    async def schedule_content_review(self, 
                                    content: Content,
                                    review_schedule: ReviewSchedule) -> ScheduledReview:
        """Schedule periodic content review."""
        
        # Calculate next review date
        next_review = self.calculate_next_review_date(
            content.created_at,
            review_schedule.frequency
        )
        
        # Create scheduled review
        scheduled_review = ScheduledReview(
            id=generate_uuid(),
            content_id=content.id,
            review_type=review_schedule.type,
            scheduled_date=next_review,
            reviewers=review_schedule.reviewers,
            checklist=review_schedule.checklist,
            status='scheduled'
        )
        
        # Schedule review task
        await self.workflow.schedule_task(
            task_type='content_review',
            scheduled_date=next_review,
            context={
                'content_id': content.id,
                'review_id': scheduled_review.id
            }
        )
        
        return scheduled_review
```

---

## 14. Output Summary

1. **Documentation Architecture** — comprehensive multi-layer architecture with AI-powered services.
2. **Knowledge Portal Design** — enterprise knowledge portal with advanced search and personalization.
3. **Learning Center Design** — interactive learning management system with courses, tutorials, and certifications.
4. **Database Schema** — 25 tables for articles, tutorials, courses, progress, and user interactions.
5. **ER Diagram** — textual representation of documentation and learning table relationships.
6. **API Specification** — 30+ endpoints for content management, search, learning, and user interactions.
7. **Backend Architecture** — scalable service architecture with AI integration and content management.
8. **Frontend Architecture** — responsive React components for documentation, learning, and administration.
9. **AI Documentation Integration** — AI-powered content generation, summarization, translation, and search.
10. **Search Strategy** — advanced search with semantic understanding, AI ranking, and personalized results.
11. **Administrator Guide** — content management, workflow configuration, and system administration.
12. **Developer Guide** — API documentation, content development, and integration guidelines.
13. **User Guide** — knowledge portal usage, learning center navigation, and personalization features.
14. **Content Governance Strategy** — content lifecycle management, quality assurance, and compliance monitoring.

All specifications are enterprise-grade, searchable, version-controlled, multilingual-ready, AI-assisted, and fully integrated into AEDIP.
