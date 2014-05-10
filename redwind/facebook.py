from . import app
from .models import Post

from flask.ext.login import login_required, current_user
from flask import request, redirect, url_for, render_template

import requests
import json


@app.route('/admin/authorize_facebook')
@login_required
def authorize_facebook():
    import urllib.parse
    import urllib.request
    redirect_uri = app.config.get('SITE_URL') + '/admin/authorize_facebook'
    params = {'client_id': app.config.get('FACEBOOK_APP_ID'),
              'redirect_uri': redirect_uri,
              'scope': 'publish_stream'}

    code = request.args.get('code')
    if code:
        params['code'] = code
        params['client_secret'] = app.config.get('FACEBOOK_APP_SECRET')

        r = urllib.request.urlopen(
            'https://graph.facebook.com/oauth/access_token?'
            + urllib.parse.urlencode(params))
        payload = urllib.parse.parse_qs(r.read())

        access_token = payload[b'access_token'][0].decode('ascii')
        current_user.facebook_access_token = access_token
        current_user.save()
        return redirect(url_for('settings'))
    else:
        return redirect('https://graph.facebook.com/oauth/authorize?'
                        + urllib.parse.urlencode(params))


@app.route('/admin/share_on_facebook', methods=['GET', 'POST'])
@login_required
def share_on_facebook():
    from .twitter import collect_images

    if request.method == 'GET':
        post = Post.load_by_shortid(request.args.get('id'))
        return render_template('share_on_facebook.html', post=post,
                               imgs=list(collect_images(post)))

    try:
        post_id = request.form.get('post_id')
        preview = request.form.get('preview')
        img_url = request.form.get('img')

        with Post.writeable(Post.shortid_to_path(post_id)) as post:
            facebook_url = handle_new_or_edit(post, preview, img_url)
            post.save()

            return """Shared on Facebook<br/>
            <a href="{}">Original</a><br/>
            <a href="{}">On Facebook</a><br/>
            """.format(post.permalink, facebook_url)

    except Exception as e:
        app.logger.exception('posting to facebook')
        return """Share on Facebook Failed!<br/>Exception: {}""".format(e)


def handle_new_or_edit(post, preview, img_url):
    app.logger.debug('publishing to facebook')

    post_args = {
        'access_token': current_user.facebook_access_token,
        'message': preview,
        'actions': json.dumps({
            'name': 'See Original',
            'link': post.permalink
        }),
        'privacy': json.dumps({'value': 'EVERYONE'})
    }

    post_args['name'] = post.title

    share_link = next(iter(post.repost_of), None)
    if share_link:
        post_args['link'] = share_link
    elif img_url:
        # if there is an image, link back to the original post,
        # and use the image as the preview image
        post_args['link'] = post.permalink
        post_args['picture'] = img_url

    response = requests.post('https://graph.facebook.com/me/feed',
                             data=post_args)

    app.logger.debug("Got response from facebook %s", response)

    if response.status_code // 100 != 2:
        raise RuntimeError("Bad response from Facebook. Status: {}, Content: {}"
                           .format(response.status_code, response.content))

    if 'json' in response.headers['content-type']:
        result = response.json()

    app.logger.debug('published to facebook. response {}'.format(result))
    if result:
        facebook_post_id = result['id']
        split = facebook_post_id.split('_', 1)
        if split and len(split) == 2:
            user_id, post_id = split
            fb_url = 'https://facebook.com/{}/posts/{}'.format(user_id, post_id)
            post.syndication.append(fb_url)
            return fb_url
