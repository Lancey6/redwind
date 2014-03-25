# Copyright © 2013, 2014 Kyle Mahan
# This file is part of Red Wind.
#
# Red Wind is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Red Wind is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Red Wind.  If not, see <http://www.gnu.org/licenses/>.



from app import app
from models import *
from views import *
from shortlinks import *

PLUGINS = ['facebook_plugin', 'twitter_plugin',
           'push_plugin', 'webmention_sender',
           'webmention_receiver']

for plugin in PLUGINS:
    importlib.import_module('plugins.' + plugin)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
