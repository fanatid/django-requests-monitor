$        = require 'jquery'
strftime = require 'jquery-strftime'
cookie   = require 'jquery-cookie'
_        = require 'underscore'
Backbone = require 'backbone'
Mustache = require 'mustache'


support_html5_storage = ->
    try
        return window['localStorage'] != null
    catch e
        return false


class RequestInfoView extends Backbone.View
    initialize: (options) ->
        @model.view = @
    render: ->
        status = @model.get "status"
        status = _.first _.filter [
            [100, 200, "info"],
            [200, 300, "success"],
            [300, 400, "redirection"],
            [400, 500, "cerror"],
            [500, 600, "serror"]
        ], (data) =>
            data[0] <= status < data[1]
        context = _.extend @model.toJSON(),
            "formated_date": ($.strftime "%d/%b/%Y %H:%M:%S.", @model.get "date") + @model.get("date").getMilliseconds()
            "request_class": if status? then status[2] else null
        @el = Mustache.render $("#tpl-requests-request").text(), context
        @$el = $(@el)
        @$el.on "click", =>
            window.location.hash = "#!/r/" + @model.get "key"
        @
    remove: ->
        @$el.remove()


class RequestInfoCollection extends Backbone.Collection
    comparator: (model) ->
        -model.get("date").getTime()
    sync: ->
        Backbone.ajax
            type: "POST"
            data:
                "keys":     @pluck "key"
                "settings": if window.settings then JSON.stringify(window.settings.toJSON()) else {}
            beforeSend: (xhr, settings) ->
                xhr.setRequestHeader "X-CSRFToken", $.cookie('csrftoken')
            success: (data, status, xhr) =>
                if data.delete? and data.delete.length > 0
                    @remove _.filter @models, (model) ->
                        model.get("key") in data.delete
                if data.new?
                    for obj in data.new
                        @add new @model
                            key:    obj.key
                            date:   new Date(obj.date)
                            method: obj.method
                            status: parseInt(obj.status)
                            path:   obj.path
    start_sync: ->
        @syncID = setInterval (=> @sync()), 1000
        @sync()
    stop_sync: ->
        clearInterval @syncID


class RequestsView extends Backbone.View
    id: "requests"
    initialize: (options) ->
        @$el.html $("#tpl-requests").text()
    render: ->
        @requests = new RequestInfoCollection
        $target = @$el.find("tbody")
        @requests.on "add", (model, collection, options) =>
            view = new RequestInfoView
                model: model
            $el = view.render().$el
            if @$el.find("tbody >").length != 0
                if @requests.last() == model
                    @$el.find("tbody > :last").after $el
                else
                    @$el.find("tbody >").eq(@requests.indexOf(model)).before $el
            else
                @$el.find("tbody").append $el
        @requests.on "remove", (model, collection, options) =>
            model.view.remove()
        @requests.start_sync()
        @gc = setInterval (=>
            keys = @requests.pluck "key"
            @$el.find("tbody tr").each ->
                if $(@).attr("id") not in keys
                    $(@).remove()
        ), 5000
        @
    remove: ->
        @requests.stop_sync()
        clearInterval(@gc)
        @$el.remove()


class RequestModel extends Backbone.Model
    urlRoot: "r"


class RequestView extends Backbone.View
    id: "request"
    initialize: (options) ->
        @$el.html $("#tpl-request").text()
        @template_title     = Mustache.compile $("#tpl-request-title").text()
        @template_content   = Mustache.compile $("#tpl-request-content").text()
        @template_response  = Mustache.compile $("#tpl-request-response").text()
        @template_tpl_src   = Mustache.compile $("#tpl-request-template-source").text()
        @template_panel_nav = Mustache.compile $("#tpl-request-panel-nav").text()
    render: ->
        @model = new RequestModel
            id: @options.key
        @model.fetch
            success: (data, status, xhr) =>
                @$el.find(".content")
                    .data("top", @$el.find(".content").css "top")
                    .data("top-iframe", @$el.find(".title").css "top")
                for panel, index in @model.get "panels"
                    $(@template_panel_nav _.extend _.clone(panel), "hash": '#!/r/' + @model.id + '/' + index)
                        .appendTo(@$el.find(".toolbar ul"))
                        .on "click", ->
                            window.router.navigate $(@).find("a").data("hash"), false
                            Backbone.history.loadUrl $(@).find("a").data("hash")
                            return false
                if @currentPanel? then @set_panel @currentPanel else @unset_panel()
            error: (xhr, status, error) =>
                $("<div class=\"alert alert-error\">Cann't load request data :'(</div>")
                    .after("#navbar")
                    .fadeIn('slow')
                    .delay(5000)
                    .fadeOut 'slow', ->
                        $(@).remove()
        @
    set_panel: (panel) ->
        @$el.find(".title, .content").children().remove()
        unless panel instanceof Object
            panel = parseInt(panel)
        unless @model.has "panels"
            @currentPanel = panel
            return
        if panel instanceof Object
            callback = panel.callback
            panel    = panel.panel
        return if isNaN(panel) or @model.get("panels").length <= panel < 0
        @currentPanel = panel
        @$el.find(".toolbar ul li").eq(panel).addClass "active"
        panel = @model.get("panels")[panel]
        @$el.find(".title")
            .show()
            .html @template_title panel
        @$el.find(".content")
            .css("top", @$el.find(".content").data("top"))
            .html @template_content panel
        # bind click event in SQL querys
        @$el.find(".query .djDebugSql").each ->
            $(@).find(".djDebugCollapsed, .djDebugUncollapsed").on "click", (event) =>
                $(event.target).hide()
                $(@).find(if "djDebugCollapsed" in $(event.target).attr("class").split(' ') then ".djDebugUncollapsed" else ".djDebugCollapsed").show()
                return false
        @$el.find(".toggle").each (index, item) =>
            $(item).find("a").on "click", (event) =>
                $el = $(event.target)
                id = $el.data "toggle-id"
                if $("#sqlDetails_"+id).is(":visible")
                    $el.html $el.data "toggle-open"
                    $("#sqlMain_"+id).find(".query .djDebugCollapsed").trigger "click"
                    $("#sqlDetails_"+id).hide()
                else
                    $el.html $el.data "toggle-close"
                    $("#sqlMain_"+id).find(".query .djDebugUncollapsed").trigger "click"
                    $("#sqlDetails_"+id).show()
        # bind template source and toggle context in Templates
        @$el.find("dl dt").each (index, item) =>
            return unless ($tag = $(item).find("a")).length
            $tag.on "click", (event) =>
                $.ajax
                    url: ($tag.attr "href").replace "/__debug__/template_source/", "t/"
                    success: (data, status, xhr) =>
                        @$el.find(".title").html @template_title title: "Template name: " + data.template_name
                        @$el.find(".content").html @template_tpl_src source: data.source
                return false
        @$el.find("dl dd").each ->
            $(@).find("a.djTemplateShowContext").on "click", =>
                $(@).find(".djTemplateHideContextDiv").toggle()
                $(@).find("span.toggleArrow").html \
                    if $(@).find(".djTemplateHideContextDiv").is(":visible") then String.fromCharCode(0x25bc) else String.fromCharCode(0x25b6)
        @$el.find(".content").show()
        callback() if callback?
    unset_panel: ->
        @$el.find(".title, .content").children().remove()
        @currentPanel = null
        @$el.find(".title")
            .hide()
        @$el.find(".content")
            .css("top", @$el.find(".content").data("top"))
            .hide()
        if @model.get 'response_content'
            @$el.find(".content")
                .css("top", @$el.find(".content").data("top-iframe"))
                .show()
                .html @template_response
                    'key': @options.key
        @$el.find(".toolbar ul li.active").removeClass "active"


class SettingsView extends Backbone.View
    id: "settings"
    initialize: (options) ->
        @settings = window.settings
    events:
        "input input[type=text]":      "save_settings"
        "change input[type=checkbox]": "save_settings"
    render: ->
        unless @settings
            @$el.html $("<h3>You browser not support HTML5 localStorage! :'(</h3>")
            return @
        @$el.html Mustache.render($("#tpl-settings").text(), @settings.toJSON())
        @
    save_settings: ->
        settings = {}
        # validate requests_count
        requests_count = @$el.find("input[name=requests_count]").removeClass("error").val()
        if requests_count
            if isNaN(parseInt(requests_count)) or parseInt(requests_count) < 0
                @$el.find("input[name=requests_count]").addClass("error")
            else
                settings.requests_count = requests_count
        else
            settings.requests_count = requests_count
        # ajax_only
        settings.ajax_only = @$el.find("input[name=ajax_only]").is ":checked"
        # request_method
        settings.request_method = @$el.find("input[name=request_method]").val()
        # request_status_code
        request_status_code = @$el.find("input[name=request_status_code]").removeClass("error").val()
        if request_status_code
            if isNaN(parseInt(request_status_code))
                @$el.find("input[name=request_status_code]").addClass("error")
            else
                settings.request_status_code = request_status_code
        else
            settings.request_status_code = request_status_code
        # save
        @settings.set settings
        if @settings.hasChanged()
            @settings.save()

class NavbarView extends Backbone.View
    initialize: (options) ->
        @ul_request  = @$el.find(".request")
        @ul_settings = @$el.find(".settings")
    set_settings: ->
        @ul_request.html $("<li><a href=\"#\">Requests</a></li>")
        @ul_settings.html $("<li>Settings</li>")
    set_requests: ->
        @ul_request.html $("<li>Requests</li>")
        @ul_settings.html $("<li><a href=\"#!/settings\">Settings</a></li>")
    set_request: (key) ->
        @ul_request
            .html($("<li><a href=\"#\">Requests</a><span class=\"divider\">/</span></li>"))
            .append $("<li>Request</li>")
        @ul_settings.html $("<li><a href=\"#!/settings\">Settings</a></li>")
    set_panel: (key, title) ->
        @ul_request
            .html($("<li><a href=\"#\">Requests</a><span class=\"divider\">/</span></li>"))
            .append($("<li><a href=\"#!/r/"+key+"\">Request</a><span class=\"divider\">/</span></li>"))
            .append $("<li>"+title+"</li>")
        @ul_settings.html $("<li><a href=\"#!/settings\">Settings</a></li>")


class AppView extends Backbone.View
    initialize: (options) ->
        @setElement $("#container")
        @navbarView = new NavbarView
            el: $("#navbar")
    load_requests: ->
        @navbarView.set_requests()
        @currentView.remove() if @currentView
        @currentView = new RequestsView
        @$el.html @currentView.render().$el
    load_request: (key) ->
        @navbarView.set_request(key)
        if @currentView? and @currentView instanceof RequestView
            @currentView.unset_panel()
            return
        @currentView.remove() if @currentView
        @currentView = new RequestView
            key: key
        @$el.html @currentView.render().$el
    load_request_panel: (key, panel) ->
        @load_request(key)
        @currentView.set_panel
            panel:    panel,
            callback: =>
                @navbarView.set_panel(key, @currentView.model.get("panels")[@currentView.currentPanel].nav_title)
    load_settings: ->
        @navbarView.set_settings()
        @currentView.remove() if @currentView
        @currentView = new SettingsView
        @$el.html @currentView.render().$el


class AppSettingsModel extends Backbone.Model
    name: "requests_monitor_settings"
    defaults:
        "requests_count":      undefined
        "ajax_only":           undefined
        "request_method":      undefined
        "request_status_code": undefined
    sync: (method, model, options) ->
        if method in ["create", "update", "patch"]
            localStorage.setItem @name, JSON.stringify(model.toJSON())
            options.success {}
        else if method == "read"
            options.success JSON.parse(localStorage.getItem @name)
        else if method == "destroy"
            localStorage.removeItem @name
            options.success()


class AppRouter extends Backbone.Router
    initialize: (options) ->
        @app = new AppView
    requests: ->
        @app.load_requests()
    request: (key) ->
        @app.load_request(key)
    panel: (key, panel) ->
        @app.load_request_panel(key, panel)
    settings: ->
        @app.load_settings()
    routes:
        "":                "requests",
        "!/r/:key":        "request",
        "!/r/:key/:panel": "panel",
        "!/settings":      "settings",

$ ->
    if support_html5_storage()
        window.settings = new AppSettingsModel
        window.settings.fetch()
    else
        window.settings = undefined
    window.router = new AppRouter
    Backbone.history.start()
