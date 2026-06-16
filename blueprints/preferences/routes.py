# blueprints/preferences/routes.py
# GET / PUT endpoints for the per-user UI preferences store. Keys are
# free-form namespaced strings (e.g., "worth_it_filter::rich-results")
# and values are arbitrary JSON-serializable structures.

import json

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from extensions import db
from models.preferences import UserPreference


preferences_bp = Blueprint(
    "preferences",
    __name__,
    template_folder=None,
    static_folder=None,
)


# Cap the key and value size to keep a malicious or buggy client from
# bloating the table. 200 chars matches the column; 32 KB is plenty
# for any reasonable preference payload.
_MAX_KEY_LEN = 200
_MAX_VALUE_BYTES = 32 * 1024


@preferences_bp.route("/api/preferences/<path:pref_key>/", methods=["GET"])
@login_required
def get_preference(pref_key):
    """
    Returns the stored value for a preference key, or {value: null} if
    nothing has been saved.

    Args:
        pref_key (str): The namespaced preference key.

    Returns:
        JSON {key, value} where value is the deserialized stored object.
    """

    if not pref_key or len(pref_key) > _MAX_KEY_LEN:
        return jsonify({"error": "Invalid pref_key"}), 400

    row = UserPreference.query.filter_by(
        user_id=current_user.id,
        pref_key=pref_key,
    ).first()

    if not row:
        return jsonify({"key": pref_key, "value": None}), 200

    try:
        value = json.loads(row.pref_value)
    except (TypeError, ValueError):

        # Stored value is corrupt — treat as missing instead of erroring
        value = None

    return jsonify({"key": pref_key, "value": value}), 200


@preferences_bp.route("/api/preferences/<path:pref_key>/", methods=["PUT"])
@login_required
def put_preference(pref_key):
    """
    Upserts the value for a preference key. The request body must be a
    JSON object with a "value" field; the value is JSON-serialized and
    stored as a string so any structure round-trips.

    Args:
        pref_key (str): The namespaced preference key.

    Returns:
        JSON success indicator.
    """

    if not pref_key or len(pref_key) > _MAX_KEY_LEN:
        return jsonify({"error": "Invalid pref_key"}), 400

    data = request.get_json(silent=True) or {}
    if "value" not in data:
        return jsonify({"error": "Body must include 'value'"}), 400

    serialized = json.dumps(data["value"], ensure_ascii=False)
    if len(serialized.encode("utf-8")) > _MAX_VALUE_BYTES:
        return jsonify({"error": "Value too large"}), 413

    row = UserPreference.query.filter_by(
        user_id=current_user.id,
        pref_key=pref_key,
    ).first()

    if row:
        row.pref_value = serialized
    else:
        row = UserPreference(
            user_id=current_user.id,
            pref_key=pref_key,
            pref_value=serialized,
        )
        db.session.add(row)

    db.session.commit()

    return jsonify({"success": True}), 200
