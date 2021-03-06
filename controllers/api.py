# These are the controllers for your ajax api.


def get_user_name_from_email(email):
    """Returns a string corresponding to the user first and last names,
    given the user email."""
    u = db(db.auth_user.email == email).select().first()
    if u is None:
        return 'None'
    else:
        return ' '.join([u.first_name, u.last_name])

@auth.requires_login()
def get_posts():
    start_idx = int(request.vars.start_idx) if request.vars.start_idx is not None else 0
    end_idx = int(request.vars.end_idx) if request.vars.end_idx is not None else 0
    selected_course_id = int(request.vars.course_id) if request.vars.course_id is not None else 0
    # We just generate a lot of of data.
    posts = []
    has_more = False
    # TODO: change query once courses data entered into db
    # post_db_rows = db((db.post.user_email == auth.user.email) & (db.post.course_id == selected_course_id))\
    #    .select(db.post.ALL,  limitby=(start_idx, end_idx + 1), orderby=~db.post.created_on)
    post_db_rows = db((db.post.user_email == auth.user.email)).select(db.post.ALL, limitby=(start_idx, end_idx + 1), orderby=~db.post.updated_on)

    for i, r in enumerate(post_db_rows):
        if i < end_idx - start_idx:
            p = generate_post(r)
            posts.append(p)
        else:
            has_more = True

    logged_in = auth.user_id is not None
    user_email = auth.user.email if logged_in else None
    return response.json(dict(
        posts=posts,
        logged_in=logged_in,
        has_more=has_more,
        user_email=user_email,
    ))


@auth.requires_login()
def search_posts():
    posts = []
    print "search posts"
    print request.vars.query
    search = request.vars.query.strip() if request.vars.query is not None else 0
    print "search is: "+search
    q = ((db.post.post_content.contains(search))
         | (db.post.topic.contains(search))
         | (db.post.tags.contains(search))
         )
    print "done with search"
    # print "q is: "+q
    rows = db(q)((db.post.user_email == auth.user.email)).select(db.post.ALL,orderby=~db.post.updated_on)
    #print rows

    for i, r in enumerate(rows):
        p = generate_post(r)
        print "post p is: "
        print (p) #debug
        posts.append(p)
    logged_in = auth.user_id is not None
    user_email = auth.user.email if logged_in else None
    #print p
    return response.json(dict(
        posts=posts,
        logged_in=logged_in,
        user_email=user_email,
    ))


# Note that we need the URL to be signed, as this changes the db.
@auth.requires_signature()
def add_post():
    post_id = db.post.insert(
        post_content=request.vars.post_content,
        topic=request.vars.topic,
        tags=request.vars.tags,
        course_id=request.vars.course_id
    )
    p_raw = db.post(post_id)
    p = generate_post(p_raw)
    return response.json(dict(post=p))


@auth.requires_signature()
def del_post():
    db(db.post.id == request.vars.post_id).delete()
    return "ok"


@auth.requires_signature()
def edit_post():

    post = db.post(db.post.id == request.vars.post_id).select().first()
    post.update_record(post_content=request.vars.post_content)

    p_raw = db.post(request.vars.post_id)
    p = generate_post(p_raw)
    return response.json(dict(post=p))


@auth.requires_signature()
def add_course():
    """adds a course name to the database and returns the course ID. course name must not match any existing name"""
    post_id = db.courses.insert(
        course_name=request.vars.course_name
    )
    new_row = db.courses(post_id)
    c = generate_course(new_row)
    return response.json(dict(course=c))


@auth.requires_login()
def get_courses():
    """returns the list of courses for the current user"""
    courses = []
    course_db_rows = db((db.courses.user_email == auth.user.email)).select(db.courses.ALL, orderby=db.courses.last_used)

    for r in course_db_rows:
        course = generate_course(r)
        courses.append(course)

    return response.json(dict(
        courses=courses
    ))


def generate_post(post_db_row):
    """generate a post dictionary from a post db row entry"""
    p = dict(
        id=post_db_row.id,
        post_content=post_db_row.post_content,
        author_email=post_db_row.user_email,
        author_name=get_user_name_from_email(post_db_row.user_email),
        created_on=post_db_row.created_on,
        updated_on=post_db_row.updated_on,
        course_id=post_db_row.course_id,
        topic=post_db_row.topic,
        tags=post_db_row.tags,
    )
    return p


def generate_course(courses_db_row):
    """generate a course dictionary from a courses db row entry"""
    c = dict(
        course_name=courses_db_row.course_name,
        created_on=courses_db_row.created_on,
        last_used=courses_db_row.last_used,
        course_id=courses_db_row.id,
    )
    return c

#gets the days between the inputted date and today
#year, month, and day need to be ints
def getDaysApart(year, month, day):
    import datetime
    today = datetime.date.today()
    someday = datetime.date(int(year), int(month), int(day))
    diff = someday - today
    #print diff.days
    return diff


@auth.requires_signature()
def add_assignments():
    print "called add assignment"
    valid= str(request.vars.due).split(" ")
    print len(valid)
    if (len(valid)!=2):
        return "invalid format"
    assign = db.t_appointment.insert(
        created_by = auth.user_id,
        f_start_time = request.vars.due,
        f_title = request.vars.assignment_name,
        description = request.vars.assignment_definition,
    )
    print request.vars.due
    print request.vars.assignment_name
    print request.vars.assignment_definition
    print assign
    slash = str(request.vars.due).split('-')  # item 0 is year, item 1 is month, item 2 is day
    day = slash[2].split(" ")
    print day[0]
    diff = getDaysApart(slash[0], slash[1], day[0])
    print diff.days
    t=dict()
    t['diff'] = int(diff.days)
    t['due']=request.vars.due
    t['assignment_name']=request.vars.assignment_name
    t['assignment_definition']=request.vars.assignment_definition
    print "done"
    print "t is:"
    print t
    return response.json(dict(assignment=t))


def get_assignments():
    print "called get_assignments"
    assignments = []
    has_more = False
    print "starting rows"
    rows = db((db.t_appointment.created_by == auth.user_id)).select(db.t_appointment.ALL,orderby=db.t_appointment.f_start_time)
    print rows
    print "finished rows"
    # need to calculate how many days until the assignment is due here
    for i, r in enumerate(rows):
            # Check if I have a track or not.
            print "due on: "
            print r.f_start_time
            slash=str(r.f_start_time).split('-') #item 0 is year, item 1 is month, item 2 is day
            print slash

            print slash[0]
            print slash[1]
            print slash[2]

            day=slash[2].split(" ")
            print day[0]
            diff=getDaysApart(slash[0],slash[1],day[0])
            print diff.days
            if(int(diff.days) >=0):
                t = dict(
                due = r.f_start_time,
                assignment_name = r.f_title,
                assignment_definition = r.description,
                id=r.id,
                diff=int(diff.days)
            )
                print t
                assignments.append(t)
    logged_in = auth.user_id is not None
    print "printing assignments"
    print assignments

    return response.json(dict(
        assignments=assignments,
        logged_in=logged_in,
        has_more=has_more,
    ))


def get_past_assignments():
    print "called get_past_assignments"
    past_assignments = []
    print "starting rows"
    rows = db((db.t_appointment.created_by == auth.user_id)).select(db.t_appointment.ALL,orderby=db.t_appointment.f_start_time)
    print "rows"
    print rows
    print "finished rows"
    # need to calculate how many days until the assignment is due here
    for i, r in enumerate(rows):
            # Check if I have a track or not.
            print "due on: "
            print r.f_start_time
            slash=str(r.f_start_time).split('-') #item 0 is year, item 1 is month, item 2 is day
            print slash

            print slash[0]
            print slash[1]
            print slash[2]

            day=slash[2].split(" ")
            print day[0]
            diff=getDaysApart(slash[0],slash[1],day[0])
            print diff.days
            if(int(diff.days) <0):
                t = dict(
                due = r.f_start_time,
                assignment_name = r.f_title,
                assignment_definition = r.description,
                id=r.id,
                diff=int(diff.days)
            )
                print t
                past_assignments.append(t)
    print "printing past_assignments"
    print past_assignments
    return response.json(dict(
        past_assignments=past_assignments,
    ))

@auth.requires_signature()
def del_assignment():
    print "called del_assignment()"
    print request.vars.track_id
    db(db.t_appointment.id == request.vars.track_id).delete()
    return "ok"